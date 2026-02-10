import SwiftUI
import os.log

final class ChatViewModel: ObservableObject {
    // MARK: - Published properties
    @Published public var messages: [Message] = []
    @Published public var inputText: String = ""
    @Published public var errorMessage: String? = nil
    @Published public var isProcessing: Bool = false
    @Published public var useWebSearch: Bool = false
    @Published public var useMemoryContext: Bool = true
    @Published public var useDarkMode: Bool = false
    @Published public var ingestStatus: ServiceStatus = .healthy
    @Published public var ollamaStatus: ServiceStatus = .disconnected
    @Published public var agentStatus: ServiceStatus = .disconnected
    @Published public var agentHealthDetails: HealthStatus? = nil
    @Published public var currentSession: ChatSession?

    @Published public var llmProvider: String = "ollama"
    
    // Add session service instance
    private let sessionService = SessionService.shared
    private let logger = SharedLogger.shared

    // MARK: - Service Health Methods
    
    /// Check if all required services are healthy
    public func areServicesHealthy() -> Bool {
        return ollamaStatus == .healthy && agentStatus == .healthy
    }
    
    /// Perform initial health check
    public func initialHealthCheck() async {
        await checkAllServices()
    }
    
    /// Check the status of all services
    public func checkAllServices() async {
        // TODO: Implement actual service health checks
        // For now, simulate checking services using AgentService
        do {
            let healthStatus = try await AgentService.shared.checkHealth()
            await MainActor.run {
                self.agentHealthDetails = healthStatus
                self.agentStatus = healthStatus.status == "healthy" ? .healthy : .disconnected
            }
        } catch {
            await MainActor.run {
                self.agentStatus = .disconnected
                self.agentHealthDetails = nil
            }
        }
        
        // Check Ollama service separately
        do {
            _ = try await LLMService.shared.listModels()
            await MainActor.run {
                self.ollamaStatus = .healthy
            }
        } catch {
            await MainActor.run {
                self.ollamaStatus = .disconnected
            }
        }
    }
    
    /// Send a message
    public func sendMessage() async {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        await MainActor.run {
            self.isProcessing = true
            let userMessage = Message(type: .user, content: inputText, timestamp: Date())
            self.messages.append(userMessage)
            self.inputText = ""
        }
        
        // Use AgentService to send the message
        do {
            let response = try await AgentService.shared.query(
                text: inputText,
                webSearch: useWebSearch,
                useMemory: useMemoryContext,
                userId: "default",
                stream: false
            )
            
            await MainActor.run {
                let assistantMessage = Message(
                    type: .assistant, 
                    content: response.response,
                    timestamp: Date(),
                    sources: response.sources,
                    toolsUsed: response.tools_used,
                    modelUsed: response.model_used,
                    processingTime: response.processing_time
                )
                self.messages.append(assistantMessage)
                self.isProcessing = false
                
                // Save the session with updated messages
                self.saveCurrentSession()
            }
        } catch {
            await MainActor.run {
                self.errorMessage = "Failed to send message: \(error.localizedDescription)"
                self.isProcessing = false
            }
        }
    }
    
    /// Regenerate the last response
    public func regenerateLastResponse() async {
        guard let lastUserMessage = messages.last(where: { $0.type == .user }) else { return }
        
        await MainActor.run {
            self.isProcessing = true
            
            // Remove the last assistant response if it exists
            if let lastMessage = messages.last, lastMessage.type == .assistant {
                messages.removeLast()
            }
        }
        
        // Regenerate using AgentService
        do {
            let response = try await AgentService.shared.query(
                text: lastUserMessage.content,
                webSearch: useWebSearch,
                useMemory: useMemoryContext,
                userId: "default",
                stream: false
            )
            
            await MainActor.run {
                let assistantMessage = Message(
                    type: .assistant, 
                    content: response.response,
                    timestamp: Date(),
                    sources: response.sources,
                    toolsUsed: response.tools_used,
                    modelUsed: response.model_used,
                    processingTime: response.processing_time
                )
                self.messages.append(assistantMessage)
                self.isProcessing = false
                
                // Save the session with updated messages
                self.saveCurrentSession()
            }
        } catch {
            await MainActor.run {
                self.errorMessage = "Failed to regenerate response: \(error.localizedDescription)"
                self.isProcessing = false
            }
        }
    }

    public func startNewSession() {
        let newSession = ChatSession(id: UUID(), title: "New Session", messages: [])
        currentSession = newSession
        messages = []

        // Update settings from new session
        llmProvider = newSession.settings.provider
        useDarkMode = newSession.settings.useDarkMode
        
        // Save the new session
        do {
            try sessionService.saveSession(newSession)
        } catch {
            logger.general.error("Failed to save new session: \(error.localizedDescription)")
        }
    }
    
    /// Loads an existing chat session.
    public func loadSession(_ session: ChatSession) {
        currentSession = session
        messages = session.messages

        // Update settings from loaded session
        llmProvider = session.settings.provider
        useDarkMode = session.settings.useDarkMode
        
        // Update toggles to match session settings
        useWebSearch = session.settings.useWebSearch
        useMemoryContext = session.settings.useMemoryContext
    }
    
    /// Uploads a document asynchronously.
    public func uploadDocument() async {
        logger.general.info("Document upload initiated")
        
        do {
            let fileURL = try FileService.shared.selectFileToUpload()
            let content = try FileService.shared.readContent(from: fileURL)
            
            let response = try await IngestService.shared.ingestDocument(
                filename: fileURL.lastPathComponent,
                content: content
            )
            
            await MainActor.run {
                self.errorMessage = "Document uploaded successfully: \(response.document_id ?? "Unknown ID")"
            }
        } catch FileError.userCancelled {
            // User cancelled, do nothing
        } catch {
            await MainActor.run {
                self.errorMessage = "Failed to upload document: \(error.localizedDescription)"
            }
        }
    }
    
    /// Saves current session settings.
    public func saveSessionSettings() {
        guard var session = currentSession else { return }
        
        session.settings.useWebSearch = useWebSearch
        session.settings.useMemoryContext = useMemoryContext
        session.settings.provider = llmProvider
        session.settings.useDarkMode = useDarkMode
        
        currentSession = session
        saveCurrentSession()
    }
    
    /// Save the current session
    private func saveCurrentSession() {
        guard let session = currentSession else { return }
        
        do {
            try sessionService.saveSession(session)
        } catch {
            logger.general.error("Failed to save session: \(error.localizedDescription)")
            errorMessage = "Failed to save session"
        }
    }
    
    /// Export current session as markdown
    public func exportAsMarkdown() {
        guard let session = currentSession else { return }
        
        do {
            _ = try FileService.shared.exportChatAsMarkdown(
                messages: messages,
                sessionTitle: session.title
            )
        } catch FileError.userCancelled {
            // User cancelled, do nothing
        } catch {
            errorMessage = "Failed to export chat: \(error.localizedDescription)"
        }
    }
}

// MARK: - Supporting Types (for ChatView compatibility)

enum ServiceStatus: String, Codable {
    case healthy = "healthy"
    case disconnected = "disconnected"
    case error = "error"
    
    var color: Color {
        switch self {
        case .healthy: return .green
        case .disconnected: return .red
        case .error: return .orange
        }
    }
    
    var displayText: String {
        rawValue.capitalized
    }
}

