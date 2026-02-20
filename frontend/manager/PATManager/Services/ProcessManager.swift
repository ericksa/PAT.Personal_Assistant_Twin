import Foundation
import SwiftUI
import Combine

/// Configuration settings for the ProcessManager
struct ProcessManagerConfiguration {
    var backendPath: String
    var pythonPath: String
    var enableHealthChecks: Bool
    var healthCheckInterval: TimeInterval
    var maxLogSize: Int
    var logRetentionSize: Int
    
    static let `default` = ProcessManagerConfiguration(
        backendPath: "/Users/adamerickson/Projects/PAT/backend",
        pythonPath: "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
        enableHealthChecks: true,
        healthCheckInterval: 30.0,
        maxLogSize: 100_000,
        logRetentionSize: 50_000
    )
}

/// Manages PAT microservice processes
@MainActor
class ProcessManager: ObservableObject {
    @Published var services: [PATService] = PATService.allServices
    @Published var combinedLogs: String = ""
    @Published var configuration: ProcessManagerConfiguration
    @Published var isHealthChecking: Bool = false
    
    private(set) var processes: [String: Process] = [:]
    private var logFileHandle: FileHandle?
    private let logFileURL: URL
    
    /// Initializes the ProcessManager with optional custom configuration
    /// - Parameter configuration: Configuration settings. Uses defaults if not provided.
    init(configuration: ProcessManagerConfiguration = .default) {
        self.configuration = configuration
        
        // Set up log file
        let docsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        self.logFileURL = docsURL.appendingPathComponent("PATManager.log")
        setupLogFile()
        
        // Load saved configuration
        loadConfiguration()
        
        // Start health checks if enabled
        if configuration.enableHealthChecks {
            startHealthChecks()
        }
    }
    
    deinit {
        logFileHandle?.closeFile()
    }
    
    // MARK: - Configuration Management
    
    private func loadConfiguration() {
        let defaults = UserDefaults.standard
        if let backendPath = defaults.string(forKey: "backendPath") {
            configuration.backendPath = backendPath
        }
        if let pythonPath = defaults.string(forKey: "pythonPath") {
            configuration.pythonPath = pythonPath
        }
        configuration.enableHealthChecks = defaults.bool(forKey: "enableHealthChecks")
        if configuration.enableHealthChecks == false && defaults.object(forKey: "enableHealthChecks") == nil {
            configuration.enableHealthChecks = true  // Default to true
        }
    }
    
    func saveConfiguration() {
        let defaults = UserDefaults.standard
        defaults.set(configuration.backendPath, forKey: "backendPath")
        defaults.set(configuration.pythonPath, forKey: "pythonPath")
        defaults.set(configuration.enableHealthChecks, forKey: "enableHealthChecks")
        
        if configuration.enableHealthChecks {
            startHealthChecks()
        } else {
            stopHealthChecks()
        }
    }
    
    // MARK: - Service Control
    
    /// Starts a specific service by ID
    /// - Parameter serviceID: The unique identifier of the service to start
    func startService(_ serviceID: String) {
        guard let index = services.firstIndex(where: { $0.id == serviceID }) else { 
            appendLog("ERROR: Service \(serviceID) not found", level: .error)
            return 
        }
        
        let service = services[index]
        
        guard processes[serviceID] == nil else {
            appendLog("Service \(service.name) is already running (PID: \(processes[serviceID]!.processIdentifier))", level: .warning)
            return
        }
        
        services[index].status = .starting
        
        Task.detached(priority: .userInitiated) { [weak self] in
            await self?.launchService(service, atIndex: index)
        }
    }
    
    private func launchService(_ service: PATService, atIndex index: Int) async {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: configuration.pythonPath)
        
        var arguments: [String] = []
        if let module = service.pythonModule {
            arguments = ["-m", module]
        } else if let script = service.scriptPath {
            arguments = [script]
        } else {
            await MainActor.run {
                services[index].status = .error("No module or script specified")
            }
            return
        }
        
        process.arguments = arguments
        process.currentDirectoryURL = URL(fileURLWithPath: configuration.backendPath)
        
        var env = ProcessInfo.processInfo.environment
        env["PYTHONPATH"] = configuration.backendPath
        env["PYTHONUNBUFFERED"] = "1"
        process.environment = env
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if let str = String(data: data, encoding: .utf8), !str.isEmpty {
                Task { @MainActor [weak self] in
                    self?.appendLog("[\(service.name)] \(str)", level: .info)
                }
            }
        }
        
        do {
            try process.run()
            
            await MainActor.run {
                processes[service.id] = process
                services[index].status = .running(health: .unknown)
                services[index].pid = process.processIdentifier
                appendLog("Started \(service.name) (PID: \(process.processIdentifier))", level: .success)
            }
            
            process.terminationHandler = { [weak self] proc in
                Task { @MainActor [weak self] in
                    guard let self = self else { return }
                    if let idx = self.services.firstIndex(where: { $0.id == service.id }) {
                        self.services[idx].status = .stopped
                        self.services[idx].pid = nil
                        self.services[idx].lastHealthCheck = nil
                    }
                    self.processes.removeValue(forKey: service.id)
                    let exitCode = proc.terminationStatus
                    let level: LogLevel = exitCode == 0 ? .info : .error
                    self.appendLog("\(service.name) stopped with exit code \(exitCode)", level: level)
                }
            }
        } catch {
            await MainActor.run {
                services[index].status = .error(error.localizedDescription)
                appendLog("CRITICAL ERROR starting \(service.name): \(error.localizedDescription)", level: .error)
                if (error as NSError).code == 13 {
                    appendLog("Permission denied. Check Python path and script permissions.", level: .error)
                }
            }
        }
    }
    
    /// Stops a specific service by ID
    /// - Parameter serviceID: The unique identifier of the service to stop
    func stopService(_ serviceID: String) {
        guard let process = processes[serviceID] else { 
            appendLog("Service \(serviceID) is not running", level: .warning)
            return 
        }
        
        process.terminate()
        appendLog("Terminating \(serviceID)...", level: .info)
        
        // Force kill after 5 seconds if still running
        let pid = process.processIdentifier
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            // Check if process is still running using signal 0
            if kill(pid, 0) == 0 {
                kill(pid, SIGKILL)
                self?.appendLog("Force killed \(serviceID)", level: .warning)
            }
        }
    }
    
    /// Starts all configured services
    func startAll() {
        appendLog("Starting all services...", level: .info)
        for service in services {
            if case .stopped = service.status {
                startService(service.id)
            }
        }
    }
    
    /// Stops all running services
    func stopAll() {
        appendLog("Stopping all services...", level: .info)
        for serviceID in processes.keys {
            stopService(serviceID)
        }
    }
    
    // MARK: - Health Checks
    
    private func startHealthChecks() {
        stopHealthChecks()
        isHealthChecking = true
        appendLog("Health checks enabled (interval: \(configuration.healthCheckInterval)s)", level: .info)
        
        // Use Task with MainActor isolation
        Task { @MainActor [weak self] in
            guard let self = self else { return }
            while self.isHealthChecking {
                await self.performHealthChecks()
                try? await Task.sleep(nanoseconds: UInt64(self.configuration.healthCheckInterval * 1_000_000_000))
            }
        }
    }
    
    private func stopHealthChecks() {
        isHealthChecking = false
        appendLog("Health checks disabled", level: .info)
    }
    
    private func performHealthChecks() async {
        for (index, service) in services.enumerated() {
            guard case .running = service.status,
                  let port = service.port,
                  let endpoint = service.healthEndpoint else {
                continue
            }
            
            let urlString = "http://localhost:\(port)\(endpoint)"
            guard let url = URL(string: urlString) else { continue }
            
            var request = URLRequest(url: url)
            request.timeoutInterval = 5
            
            do {
                let (_, response) = try await URLSession.shared.data(for: request)
                if let httpResponse = response as? HTTPURLResponse {
                    let health: ServiceHealth = (200...299).contains(httpResponse.statusCode) 
                        ? .healthy 
                        : .unhealthy("HTTP \(httpResponse.statusCode)")
                    await MainActor.run {
                        services[index].status = .running(health: health)
                        services[index].lastHealthCheck = Date()
                    }
                }
            } catch {
                await MainActor.run {
                    services[index].status = .running(health: .unhealthy(error.localizedDescription))
                }
            }
        }
    }
    
    // MARK: - Logging
    
    enum LogLevel: String, CaseIterable {
        case debug = "DEBUG"
        case info = "INFO"
        case success = "SUCCESS"
        case warning = "WARN"
        case error = "ERROR"
        
        var color: String {
            switch self {
            case .debug: return "\u{001B}[90m"  // Gray
            case .info: return "\u{001B}[0m"     // Default
            case .success: return "\u{001B}[32m" // Green
            case .warning: return "\u{001B}[33m" // Yellow
            case .error: return "\u{001B}[31m"   // Red
            }
        }
    }
    
    private func setupLogFile() {
        if !FileManager.default.fileExists(atPath: logFileURL.path) {
            FileManager.default.createFile(atPath: logFileURL.path, contents: nil, attributes: nil)
        }
        logFileHandle = try? FileHandle(forWritingTo: logFileURL)
        logFileHandle?.seekToEndOfFile()
    }
    
    private func appendLog(_ message: String, level: LogLevel = .info) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let logEntry = "[\(timestamp)] [\(level.rawValue)] \(message)\n"
        
        // Update UI logs
        combinedLogs += logEntry
        if combinedLogs.count > configuration.maxLogSize {
            combinedLogs = String(combinedLogs.suffix(configuration.logRetentionSize))
        }
        
        // Write to file
        if let data = logEntry.data(using: .utf8) {
            logFileHandle?.write(data)
        }
        
        // Print to console for debugging
        print(logEntry, terminator: "")
    }
    
    /// Clears all logs from memory
    func clearLogs() {
        combinedLogs = ""
        appendLog("Logs cleared", level: .info)
    }
    
    /// Exports logs to a file
    /// - Returns: URL of the exported file, or nil if export failed
    func exportLogs() -> URL? {
        let exportURL = logFileURL.deletingLastPathComponent()
            .appendingPathComponent("PATManager_export_\(ISO8601DateFormatter().string(from: Date())).log")
        
        do {
            try combinedLogs.write(to: exportURL, atomically: true, encoding: .utf8)
            return exportURL
        } catch {
            appendLog("Failed to export logs: \(error.localizedDescription)", level: .error)
            return nil
        }
    }
}

// MARK: - Extensions

extension ServiceStatus {
    var indicator: String {
        switch self {
        case .stopped: return "○"
        case .starting: return "◍"
        case .running(let health):
            switch health {
            case .healthy: return "●"
            case .unhealthy: return "◐"
            case .unknown: return "◍"
            }
        case .error: return "⚠"
        }
    }
}
