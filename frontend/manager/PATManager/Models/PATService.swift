import Foundation

/// Represents the current state of a service
enum ServiceStatus: Equatable {
    case stopped
    case starting
    case running(health: ServiceHealth)
    case error(String)
    
    var iconName: String {
        switch self {
        case .stopped: return "stop.circle.fill"
        case .starting: return "arrow.clockwise.circle.fill"
        case .running: return "play.circle.fill"
        case .error: return "exclamationmark.triangle.fill"
        }
    }
    
    var isRunning: Bool {
        if case .running = self { return true }
        return false
    }
}

/// Health status of a running service
enum ServiceHealth: Equatable {
    case healthy
    case unhealthy(String)
    case unknown
}

/// Represents a PAT microservice that can be managed
struct PATService: Identifiable, Equatable {
    let id: String
    let name: String
    let description: String
    let port: Int?
    let pythonModule: String?
    let scriptPath: String?
    let healthEndpoint: String?
    var status: ServiceStatus = .stopped
    var pid: Int32?
    var lastHealthCheck: Date?
    
    /// Predefined services configuration
    static let allServices: [PATService] = [
        PATService(
            id: "core",
            name: "Core API",
            description: "Main backend API and business logic",
            port: 8010,
            pythonModule: "src.main_pat",
            scriptPath: nil,
            healthEndpoint: "/health"
        ),
        PATService(
            id: "sync",
            name: "Sync Worker",
            description: "Background Apple Mail/Reminders sync",
            port: nil,
            pythonModule: nil,
            scriptPath: "scripts/pat_sync_worker.py",
            healthEndpoint: nil
        ),
        PATService(
            id: "mcp",
            name: "MCP Server",
            description: "Multi-Chain Planning & RAG orchestration",
            port: 8003,
            pythonModule: "services.mcp.app",
            scriptPath: nil,
            healthEndpoint: "/health"
        ),
        PATService(
            id: "whisper",
            name: "Whisper Service",
            description: "Voice transcription and audio processing",
            port: 8004,
            pythonModule: "services.whisper.app",
            scriptPath: nil,
            healthEndpoint: "/health"
        ),
        PATService(
            id: "teleprompter",
            name: "Teleprompter",
            description: "Interview UI and display service",
            port: 8005,
            pythonModule: "services.teleprompter.app",
            scriptPath: nil,
            healthEndpoint: "/health"
        ),
        PATService(
            id: "jobs",
            name: "Job Search",
            description: "Automated job crawling and classification",
            port: 8007,
            pythonModule: "services.jobs.app",
            scriptPath: nil,
            healthEndpoint: "/health"
        ),
        PATService(
            id: "listening",
            name: "Interview Listener",
            description: "Live audio capture and transcription",
            port: nil,
            pythonModule: nil,
            scriptPath: "services/listening/live_interview_listener.py",
            healthEndpoint: nil
        )
    ]
}
