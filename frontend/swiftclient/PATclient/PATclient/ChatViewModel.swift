import SwiftUI
import Foundation
import os.log
internal import Combine

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
    
    // MARK: - Teleprompter & WebSocket Status
    @Published public var isWebSocketConnected: Bool = false
    @Published public var isListeningActive: Bool = false
    @Published public var isTeleprompterActive: Bool = false
    @Published public var teleprompterStatusText: String = "Stopped"
    @Published public var listeningServiceStatusText: String = "Inactive"
    @Published public var webSocketStatusText: String = "Disconnected"
    
    var listeningServiceStatusColor: Color {
        isListeningActive ? .green : .gray
    }
    
    var webSocketStatusColor: Color {
        isWebSocketConnected ? .green : .orange
    }
    
    var teleprompterStatusColor: Color {
        isTeleprompterActive ? .green : .gray
    }
    
    @Published var currentSession: ChatSession?
    
    // MARK: - Dependencies
    let agentService = AgentService.shared
    let sessionService = SessionService.shared
    let llmService = LLMService.shared
    
    // Add this property to ChatViewModel class
    private let logger = SharedLogger.shared
    
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
            errorMessage = errorMsg
            return
        }
        
        // Clear any previous error
        errorMessage = nil
        inputText = ""
        
        // Add user message
        let userMessage = Message(type: .user, content: text)
        messages.append(userMessage)
        currentSession?.messages.append(userMessage)
        
        // Update session title if first message
        if currentSession?.messages.count == 1 {
            currentSession?.title = String(text.prefix(50))
            logger.general.info("New session created with title: \(self.currentSession?.title ?? "Untitled")")
        }
        
        saveSessionSettings()
        
        isProcessing = true
        
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
            
            let assistantMessage = Message(
                type: .assistant,
                content: response.response,
                sources: response.sources,
                toolsUsed: response.tools_used,
                modelUsed: response.model_used,
                processingTime: response.processing_time
            )
            
            messages.append(assistantMessage)
            currentSession?.messages.append(assistantMessage)
            currentSession?.updatedAt = Date()
            
            // Auto-save
            if let session = currentSession {
                try? sessionService.saveSession(session)
            }
            
        } catch {
            logger.logError(error, context: "Agent query failed")
            handleSendError(error)
        }
        
        isProcessing = false
    }
    
    // MARK: - Teleprompter & WebSocket Controls
    
    /// Toggle WebSocket connection for real-time text pushing
    func toggleWebSocketConnection() {
        if isWebSocketConnected {
            disconnectWebSocket()
        } else {
            connectWebSocket()
        }
    }
    
    /// Connect to WebSocket server
    func connectWebSocket() {
        // For now, just update the state
        // WebSocket client will be implemented separately
        isWebSocketConnected = true
        webSocketStatusText = "Connecting..."
        
        // Simulate connection process
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            self.webSocketStatusText = "Connected to localhost:8765"
        }
        
        logger.general.info("WebSocket connection initiated")
    }
    
    /// Disconnect from WebSocket server
    func disconnectWebSocket() {
        isWebSocketConnected = false
        webSocketStatusText = "Disconnected"
        logger.general.info("WebSocket connection terminated")
    }
    
    /// Toggle listening service (microphone)
    func toggleListeningService() {
        if isListeningActive {
            stopListeningService()
        } else {
            startListeningService()
        }
    }
    
    /// Start the Python listening service
    func startListeningService() {
        isListeningActive = true
        listeningServiceStatusText = "Starting..."
        
        // Start listening service process
        let task = Process()
        task.launchPath = "/usr/bin/env"
        task.arguments = ["python3", "/Users/adamerickson/Projects/PAT/backend/services/listening/live_interview_listener_fixed.py"]
        
        do {
            task.launch()
            listeningServiceStatusText = "Listening active"
            logger.general.info("Listening service started")
        } catch {
            listeningServiceStatusText = "Error"
            errorMessage = "Failed to start listening service: \(error.localizedDescription)"
            isListeningActive = false
            logger.general.error("Listening service failed to start: \(error)")
        }
    }
    
    /// Stop the listening service
    func stopListeningService() {
        isListeningActive = false
        listeningServiceStatusText = "Inactive"
        logger.general.info("Listening service stopped")
    }
    
    /// Toggle teleprompter visibility
    func toggleTeleprompter() {
        isTeleprompterActive.toggle()
        
        if isTeleprompterActive {
            teleprompterStatusText = "Running"
            launchTeleprompterOverlay()
        } else {
            teleprompterStatusText = "Stopped"
        }
    }
    
    /// Launch the teleprompter overlay
    func launchTeleprompterOverlay() {
        let overlayURL = URL(fileURLWithPath: "/Users/adamerickson/Projects/PAT/frontend/swiftclient/SwiftOverlayExported/PATOverlay.app")
        
        if FileManager.default.fileExists(atPath: overlayURL.path) {
            do {
                _ = try NSWorkspace.shared.open(overlayURL)
            } catch {
                errorMessage = "Failed to launch teleprompter: \(error.localizedDescription)"
                isTeleprompterActive = false
                teleprompterStatusText = "Error"
                logger.general.error("Teleprompter launch failed: \(error)")
            }
        } else {
            errorMessage = "Teleprompter not found: \(overlayURL.path)"
            isTeleprompterActive = false
            teleprompterStatusText = "Not Found"
            logger.general.error("Teleprompter app not found: \(overlayURL.path)")
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
    
    // MARK: - Public stub methods (TODO)
    
    /// Returns true if all required services are healthy.
    public func areServicesHealthy() -> Bool {
        // TODO: Implement actual health checks
        return ollamaStatus == .healthy && agentStatus == .healthy && ingestStatus == .healthy
    }
    
    /// Performs initial health checks for all services asynchronously.
    public func initialHealthCheck() async {
        await checkAllServices()
    }
    
    public func checkAllServices() async {
        let (ollamaStat, ollamaHealth) = await checkOllamaService()
        let agentHealth: HealthStatus?
        do {
            agentHealth = try await agentService.checkHealth()
        } catch {
            agentHealth = nil
        }
        
        DispatchQueue.main.async {
            self.ollamaStatus = ollamaStat
            self.agentHealthDetails = agentHealth
            self.agentStatus = agentHealth != nil ? .healthy : .disconnected
        }
    }

    
    public func startNewSession() {
        let newSession = ChatSession(id: UUID(), title: "New Session", messages: [])
        currentSession = newSession
        messages = []
        if let currentSession = currentSession {
            messages.append(contentsOf: currentSession.messages)
        }
    }
    
    /// Loads an existing chat session.
    public func loadSession(_ session: ChatSession) {
        currentSession = session
        messages = session.messages
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
            try? sessionService.saveSession(session)
        }
    }
    
    /// Determines whether to recheck service health before sending a message.
    public func shouldRecheckHealth() -> Bool {
        return ollamaStatus != .healthy || agentStatus != .healthy || ingestStatus != .healthy
    }
    
    /// Returns instructions on how to fix service availability issues.
    public func getFixInstructions() -> String {
        // TODO: Provide user-friendly fix instructions
        return "Please check your network connection and service configuration."
    }
    
    /// Handles errors that occur when sending a message.
    public func handleSendError(_ error: Error) {
        // TODO: Implement error handling logic for sending messages
        errorMessage = "Failed to send message: \(error.localizedDescription)"
    }
}
