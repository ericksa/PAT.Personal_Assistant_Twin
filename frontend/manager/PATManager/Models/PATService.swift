import Foundation

enum ServiceStatus {
    case stopped
    case starting
    case running
    case error(String)
    
    var iconName: String {
        switch self {
        case .stopped: return "stop.circle.fill"
        case .starting: return "arrow.clockwise.circle.fill"
        case .running: return "play.circle.fill"
        case .error: return "exclamationmark.triangle.fill"
        }
    }
}

struct PATService: Identifiable {
    let id: String
    let name: String
    let description: String
    let port: Int?
    let pythonModule: String?
    let scriptPath: String?
    var status: ServiceStatus = .stopped
    var pid: Int32?
    
    static let allServices: [PATService] = [
        PATService(id: "core", name: "Core API", description: "Main backend API and business logic", port: 8010, pythonModule: "src.main_pat", scriptPath: nil),
        PATService(id: "sync", name: "Sync Worker", description: "Background Apple Mail/Reminders sync", port: nil, pythonModule: nil, scriptPath: "scripts/pat_sync_worker.py"),
        PATService(id: "mcp", name: "MCP Server", description: "Multi-Chain Planning & RAG orchestration", port: 8003, pythonModule: "services.mcp.app", scriptPath: nil),
        PATService(id: "whisper", name: "Whisper Service", description: "Voice transcription and audio processing", port: 8004, pythonModule: "services.whisper.app", scriptPath: nil),
        PATService(id: "teleprompter", name: "Teleprompter", description: "Interview UI and display service", port: 8005, pythonModule: "services.teleprompter.app", scriptPath: nil),
        PATService(id: "jobs", name: "Job Search", description: "Automated job crawling and classification", port: 8007, pythonModule: "services.jobs.app", scriptPath: nil),
        PATService(id: "listening", name: "Interview Listener", description: "Live audio capture and transcription", port: nil, pythonModule: nil, scriptPath: "services/listening/live_interview_listener.py")
    ]
}
