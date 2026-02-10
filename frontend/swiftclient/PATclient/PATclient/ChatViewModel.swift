import SwiftUI
import Foundation
import os.log
import Combine

enum ServiceStatus: String, Codable, CaseIterable {
    case healthy
    case unhealthy
    case disconnected
    case error
    
    var color: Color {
        switch self {
        case .healthy:
            return .green
        case .unhealthy:
            return .orange
        case .disconnected:
            return .red
        case .error:
            return .gray
        }
    }
    
    var displayText: String {
        switch self {
        case .healthy:
            return "Healthy"
        case .unhealthy:
            return "Unhealthy"
        case .disconnected:
            return "Disconnected"
        case .error:
            return "Error"
        }
    }
}

final class ChatViewModel: ObservableObject {
    // MARK: - Published properties
    @Published public var messages: [Message] = []
    @Published public var inputText: String = ""
    @Published public var errorMessage: String? = nil
    @Published public var isProcessing: Bool = false
    @Published public var useWebSearch: Bool = false
    @Published public var useMemoryContext: Bool = true
    @Published public var ingestStatus: ServiceStatus = .healthy
    @Published public var ollamaStatus: ServiceStatus = .disconnected
    @Published public var agentStatus: ServiceStatus = .disconnected
    @Published public var agentHealthDetails: HealthStatus? = nil
    @Published var currentSession: ChatSession?

    // ✅ NEW: Add published llmProvider, synchronized with session settings
    @Published var llmProvider: String {
        didSet {
            // Keep session settings in sync
            currentSession?.settings.provider = llmProvider
        }
    }

    // MARK: - Dependencies
    let agentService: AgentService
    let sessionService: SessionService
    let llmService: LLMService
    
    // Add this property to ChatViewModel class
    private let logger: SharedLogger
    
    // MARK: - Initialization
    
    init(
        agentService: AgentService = .shared,
        sessionService: SessionService = .shared,
        llmService: LLMService = .shared,
        logger: SharedLogger = .shared
    ) {
        self.agentService = agentService
        self.sessionService = sessionService
        self.llmService = llmService
        self.logger = logger
        
        // Initialize a default session
        startNewSession()
        Task {
            await initialHealthCheck()
        }
    }
    
    // MARK: - Public methods
    
    /// Sends the current inputText to the agent asynchronously.
    func sendMessage() async {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        
        logger.agent.info("Sending message: \(text.prefix(50))...")
        
        // Check health before sending if needed
        if shouldRecheckHealth() {
            logger.agent.info("Rechecking service health before sending")
            await checkAllServices()
        }
        
        guard areServicesHealthy() else {
            let errorMsg = "Cannot send message: Services are not available\n\(getFixInstructions())"
            logger.agent.error("Services not healthy: ollama=\(self.ollamaStatus.rawValue), agent=\(self.agentStatus.rawValue)")
            await MainActor.run {
                errorMessage = errorMsg
            }
            return
        }
        
        // Clear any previous error
        await MainActor.run {
            errorMessage = nil
            inputText = ""
        }
        
        // Add user message - FIXED initialization
        let userMessage = Message(type: .user, content: text)
        await MainActor.run {
            messages.append(userMessage)
            currentSession?.messages.append(userMessage)
            
            // Update session title if first message
            if currentSession?.messages.count == 1 {
                currentSession?.title = String(text.prefix(50))
                logger.general.info("New session created with title: \(self.currentSession?.title ?? "Untitled")")
            }
        }
        
        saveSessionSettings()
        
        await MainActor.run {
            isProcessing = true
        }
        
        do {
            let startTime = Date()
            let response = try await agentService.query(
                text: text,
                webSearch: useWebSearch,
                useMemory: useMemoryContext,
                userId: currentSession?.id.uuidString ?? "anonymous"
            )
            let responseTime = Date().timeIntervalSince(startTime)
            
            logger.agent.info("Query successful in \(String(format: "%.2f", responseTime))s")
            logger.agent.debug("Response: \(response.response.prefix(100))...")
            logger.agent.debug("Tools used: \(response.tools_used.joined(separator: ", "))")
            logger.agent.debug("Sources count: \(response.sources.count)")
            
            // FIXED initialization with all required parameters
            let assistantMessage = Message(
                type: .assistant,
                content: response.response,
                sources: response.sources,
                toolsUsed: response.tools_used,
                modelUsed: response.model_used,
                processingTime: response.processing_time
            )
            
            await MainActor.run {
                messages.append(assistantMessage)
                currentSession?.messages.append(assistantMessage)
                currentSession?.updatedAt = Date()
            }
            
            // Auto-save
            if let session = currentSession {
                try? sessionService.saveSession(session)
            }
            
        } catch {
            logger.logError(error, context: "Agent query failed")
            await handleSendError(error)
        }
        
        await MainActor.run {
            isProcessing = false
        }
    }
    
    /// Checks the Ollama service health asynchronously.
    private func checkOllamaService() async -> (ServiceStatus, HealthStatus?) {
        logger.ollama.info("Checking Ollama service health")
        
        do {
            let models = try await llmService.listModels()
            if models.isEmpty {
                return (.unhealthy, nil)
            }
            return (.healthy, nil)
        } catch let error as LLMError {
            switch error {
            case .networkError:
                return (.disconnected, nil)
            case .serverError:
                return (.unhealthy, nil)
            default:
                return (.error, nil)
            }
        } catch {
            return (.error, nil)
        }
    }
    
    // MARK: - Service Health Methods
    
    /// Returns true if all required services are healthy.
    public func areServicesHealthy() -> Bool {
        return ollamaStatus == .healthy && agentStatus == .healthy
    }
    
    /// Performs initial health checks for all services asynchronously.
    public func initialHealthCheck() async {
        await checkAllServices()
    }
    
    public func checkAllServices() async {
        // FIXED: Using '_' for unused variable ollamaHealth
        let (ollamaStat, _) = await checkOllamaService()
        let agentHealth: HealthStatus?
        do {
            agentHealth = try await agentService.checkHealth()
        } catch {
            agentHealth = nil
        }
        
        await MainActor.run {
            self.ollamaStatus = ollamaStat
            self.agentHealthDetails = agentHealth
            self.agentStatus = agentHealth != nil ? .healthy : .disconnected
        }
    }

    
    public func startNewSession() {
        let newSession = ChatSession(id: UUID(), title: "New Session", messages: [])
        currentSession = newSession
        messages = []

        // ✅ Initialize llmProvider from session settings
        self.llmProvider = newSession.settings.provider
    }
    
    /// Loads an existing chat session.
    public func loadSession(_ session: ChatSession) {
        currentSession = session
        messages = session.messages

        // ✅ Initialize llmProvider from session settings
        self.llmProvider = session.settings.provider
    }
    
    /// Exports the current session as markdown.
    public func exportAsMarkdown() {
        guard let session = currentSession else {
            print("No session to export")
            return
        }
        var markdown = "# \(session.title)\n\n"
        for message in session.messages {
            switch message.type {
            case .user:
                markdown += "## User\n\(message.content)\n\n"
            case .assistant:
                markdown += "## Assistant\n\(message.content)\n\n"
                if !message.sources.isEmpty {
                    markdown += "### Sources\n"
                    for source in message.sources {
                        markdown += "- \(source)\n"
                    }
                    markdown += "\n"
                }
            case .system:
                markdown += "## System\n\(message.content)\n\n"
            }
        }
        print(markdown)
    }
    
    /// Uploads a document asynchronously.
    public func uploadDocument() async {
        print("Document upload functionality not yet implemented.")
    }
    
    /// Regenerates the last response asynchronously.
    public func regenerateLastResponse() async {
        guard !messages.isEmpty else { return }
        // Remove last assistant message
        if let lastIndex = messages.lastIndex(where: { $0.type == .assistant }) {
            messages.remove(at: lastIndex)
            currentSession?.messages.remove(at: lastIndex)
        }
        // Resend the last user input text if available
        if let lastUserMessage = messages.last(where: { $0.type == .user }) {
            inputText = lastUserMessage.content
            await sendMessage()
        }
    }
    
    /// Saves current session settings.
    public func saveSessionSettings() {
        if let session = currentSession {
            // ✅ Keep session settings in sync with published properties
            session.settings.useWebSearch = useWebSearch
            session.settings.useMemoryContext = useMemoryContext
            session.settings.provider = llmProvider
            try? sessionService.saveSession(session)
        }
    }
    
    /// Determines whether to recheck service health before sending a message.
    public func shouldRecheckHealth() -> Bool {
        return ollamaStatus != .healthy || agentStatus != .healthy || ingestStatus != .healthy
    }
    
    /// Returns instructions on how to fix service availability issues.
    public func getFixInstructions() -> String {
        var instructions: [String] = []
        
        if ollamaStatus != .healthy {
            instructions.append("• Ensure Ollama is running on http://127.0.0.1:11434")
            instructions.append("• Check that Ollama has models available")
        }
        
        if agentStatus != .healthy {
            instructions.append("• Ensure the agent service is running on http://127.0.0.1:8002")
            instructions.append("• Verify the agent service is responding to health checks")
        }
        
        return instructions.joined(separator: "\n")
    }
    
    /// Handles errors that occur when sending a message.
    public func handleSendError(_ error: Error) async {
        let errorMessage: String
        
        if let agentError = error as? AgentError {
            switch agentError {
            case .networkError(let underlyingError):
                errorMessage = "Network error: \(underlyingError.localizedDescription)"
            case .serverError(let code):
                errorMessage = "Agent server error (HTTP \(code))"
            case .invalidURL:
                errorMessage = "Invalid agent service URL"
            case .invalidResponse:
                errorMessage = "Invalid response from agent service"
            case .decodingError:
                errorMessage = "Failed to parse agent response"
            }
        } else if let llmError = error as? LLMError {
            switch llmError {
            case .networkError(let underlyingError):
                errorMessage = "LLM network error: \(underlyingError.localizedDescription)"
            case .serverError(let code):
                errorMessage = "Ollama server error (HTTP \(code))"
            case .invalidURL:
                errorMessage = "Invalid Ollama URL"
            case .decodingError(let decodingError):
                errorMessage = "Failed to parse Ollama response: \(decodingError.localizedDescription)"
            }
        } else {
            errorMessage = "Failed to send message: \(error.localizedDescription)"
        }
        
        await MainActor.run {
            self.errorMessage = errorMessage
        }
    }
}
