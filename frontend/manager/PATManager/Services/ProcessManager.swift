import Foundation
import SwiftUI
import Combine

class ProcessManager: ObservableObject {
    @Published var services: [PATService] = PATService.allServices
    @Published var combinedLogs: String = ""
    
    private var processes: [String: Process] = [:]
    private let backendPath = "/Users/adamerickson/Projects/PAT/backend"
    private let pythonPath = "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
    
    func startService(_ serviceID: String) {
        guard let index = services.firstIndex(where: { $0.id == serviceID }) else { return }
        let service = services[index]
        
        if processes[serviceID] != nil {
            appendLog("Service \(service.name) is already running.")
            return
        }
        
        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        
        var arguments: [String] = []
        if let module = service.pythonModule {
            arguments = ["-m", module]
        } else if let script = service.scriptPath {
            arguments = [script]
        }
        
        process.arguments = arguments
        process.currentDirectoryURL = URL(fileURLWithPath: backendPath)
        
        var env = ProcessInfo.processInfo.environment
        env["PYTHONPATH"] = backendPath
        env["PYTHONUNBUFFERED"] = "1"
        process.environment = env
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if let str = String(data: data, encoding: .utf8), !str.isEmpty {
                DispatchQueue.main.async {
                    self?.appendLog("[\(service.name)] \(str)")
                }
            }
        }
        
        do {
            try process.run()
            processes[serviceID] = process
            services[index].status = .running
            services[index].pid = process.processIdentifier
            appendLog("Started \(service.name) (PID: \(process.processIdentifier))")
            
            process.terminationHandler = { [weak self] proc in
                DispatchQueue.main.async {
                    self?.services[index].status = .stopped
                    self?.services[index].pid = nil
                    self?.processes.removeValue(forKey: serviceID)
                    self?.appendLog("\(service.name) stopped with exit code \(proc.terminationStatus)")
                }
            }
        } catch {
            services[index].status = .error(error.localizedDescription)
            appendLog("CRITICAL ERROR starting \(service.name): \(error.localizedDescription)")
            appendLog("Note: If you see 'Permission Denied', disable 'App Sandbox' in Xcode.")
        }
    }
    
    func stopService(_ serviceID: String) {
        guard let process = processes[serviceID] else { return }
        process.terminate()
        appendLog("Terminating \(serviceID)...")
    }
    
    func startAll() {
        for service in services {
            startService(service.id)
        }
    }
    
    func stopAll() {
        for serviceID in processes.keys {
            stopService(serviceID)
        }
    }
    
    private func appendLog(_ message: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        combinedLogs += "[\(timestamp)] \(message)\n"
        
        if combinedLogs.count > 50000 {
            combinedLogs = String(combinedLogs.suffix(25000))
        }
    }
}
