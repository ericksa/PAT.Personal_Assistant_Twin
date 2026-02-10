// Add this import at the top if not already present
import SwiftUI

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

    @Published public var llmProvider: String = "ollama" // Fixed: Set default to valid value

    // ... rest of existing properties ...

    public func startNewSession() {
        let newSession = ChatSession(id: UUID(), title: "New Session", messages: [])
        currentSession = newSession
        messages = []

        // ✅ Update settings from new session
        llmProvider = newSession.settings.provider
        useDarkMode = newSession.settings.useDarkMode
    }
    
    /// Loads an existing chat session.
    public func loadSession(_ session: ChatSession) {
        currentSession = session
        messages = session.messages

        // ✅ Update settings from loaded session
        llmProvider = session.settings.provider
        useDarkMode = session.settings.useDarkMode
    }
    
    /// Uploads a document asynchronously.
    public func uploadDocument() async {
        logger.general.info("Document upload initiated")
        
        // TODO: Implement actual document picker and upload logic
        // For now, show placeholder functionality
        await MainActor.run {
            self.errorMessage = "Document upload functionality coming soon"
        }
        
        // Simulate upload process
        try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    }
    
    /// Saves current session settings.
    public func saveSessionSettings() {
        guard var session = currentSession else { return }
        
        session.settings.useWebSearch = useWebSearch
        session.settings.useMemoryContext = useMemoryContext
        session.settings.provider = llmProvider
        session.settings.useDarkMode = useDarkMode // Added dark mode saving
        
        currentSession = session
        try? sessionService.saveSession(session)
    }

    // ... rest of existing methods ...
}
