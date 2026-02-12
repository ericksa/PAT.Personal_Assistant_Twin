import Foundation
import Combine

class ServiceRunner: ObservableObject {
    @Published var isApiRunning = false
    @Published var isSyncWorkerRunning = false
    @Published var apiLogs = ""
    @Published var syncWorkerLogs = ""
    
    private var apiProcess: Process?
    private var syncWorkerProcess: Process?
    
    private let projectPath = "/Users/adamerickson/Projects/PAT/backend"
    private let pythonPath = "/usr/bin/python3" // Standard macOS location, might need adjustment
    
    func toggleApi() {
        if isApiRunning {
            stopApi()
        } else {
            startApi()
        }
    }
    
    func toggleSyncWorker() {
        if isSyncWorkerRunning {
            stopSyncWorker()
        } else {
            startSyncWorker()
        }
    }
    
    private func startApi() {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = ["-m", "src.main_pat"]
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)
        
        let env = ProcessInfo.processInfo.environment
        var newEnv = env
        newEnv["PYTHONPATH"] = projectPath
        process.environment = newEnv
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if let str = String(data: data, encoding: .utf8) {
                DispatchQueue.main.async {
                    self?.apiLogs += str
                    if (self?.apiLogs.count ?? 0) > 10000 {
                        self?.apiLogs = String((self?.apiLogs.suffix(5000))!)
                    }
                }
            }
        }
        
        do {
            try process.run()
            self.apiProcess = process
            self.isApiRunning = true
            
            process.terminationHandler = { [weak self] _ in
                DispatchQueue.main.async {
                    self?.isApiRunning = false
                    self?.apiProcess = nil
                }
            }
        } catch {
            apiLogs += "Failed to start API: \(error)\n"
        }
    }
    
    private func stopApi() {
        apiProcess?.terminate()
    }
    
    private func startSyncWorker() {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = ["scripts/pat_sync_worker.py"]
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)
        
        let env = ProcessInfo.processInfo.environment
        var newEnv = env
        newEnv["PYTHONPATH"] = projectPath
        process.environment = newEnv
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if let str = String(data: data, encoding: .utf8) {
                DispatchQueue.main.async {
                    self?.syncWorkerLogs += str
                    if (self?.syncWorkerLogs.count ?? 0) > 10000 {
                        self?.syncWorkerLogs = String((self?.syncWorkerLogs.suffix(5000))!)
                    }
                }
            }
        }
        
        do {
            try process.run()
            self.syncWorkerProcess = process
            self.isSyncWorkerRunning = true
            
            process.terminationHandler = { [weak self] _ in
                DispatchQueue.main.async {
                    self?.isSyncWorkerRunning = false
                    self?.syncWorkerProcess = nil
                }
            }
        } catch {
            syncWorkerLogs += "Failed to start Sync Worker: \(error)\n"
        }
    }
    
    private func stopSyncWorker() {
        syncWorkerProcess?.terminate()
    }
    
    func runTests(completion: @escaping (String) -> Void) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["scripts/test_pat_api.sh"]
        process.currentDirectoryURL = URL(fileURLWithPath: projectPath)
        
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        
        do {
            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            if let output = String(data: data, encoding: .utf8) {
                completion(output)
            }
        } catch {
            completion("Test execution failed: \(error)")
        }
    }
}
