import Foundation
import os.log

class SharedLogger {
    static let shared = SharedLogger()
    
    // Create loggers for different subsystems
    let general = Logger(subsystem: "com.patclient", category: "General")
    let network = Logger(subsystem: "com.patclient", category: "Network")
    let agent = Logger(subsystem: "com.patclient", category: "Agent")
    let ingest = Logger(subsystem: "com.patclient", category: "Ingest")
    let ui = Logger(subsystem: "com.patclient", category: "UI")
    let ollama = Logger(subsystem: "com.patclient", category: "Ollama")
    
    private init() {}
    
    // Helper methods for structured logging
    func logNetworkRequest(_ url: String, method: String = "GET", body: String? = nil) {
        var details: [String: Any] = ["method": method, "url": url]
        if let body = body {
            details["body"] = body.replacingOccurrences(of: "\n", with: "\\n")
        }
        network.debug("Network Request: \(method) \(url)")
    }
    
    func logNetworkResponse(_ url: String, statusCode: Int, responseTime: TimeInterval) {
        network.info("Network Response: \(statusCode) for \(url) in \(String(format: "%.3f", responseTime))s")
    }
    
    func logError(_ error: Error, context: String) {
        _ = [
            "context": context,
            "error": String(reflecting: error),
            "localized": error.localizedDescription
        ]
        general.error("Error: \(context) - \(error.localizedDescription)")
    }
}
