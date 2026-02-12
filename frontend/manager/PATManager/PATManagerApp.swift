import SwiftUI

@main
struct PATManagerApp: App {
    @StateObject private var manager = ProcessManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Start All Services") {
                    manager.startAll()
                }
                .keyboardShortcut("s", modifiers: [.command, .shift])
                
                Button("Stop All Services") {
                    manager.stopAll()
                }
                .keyboardShortcut("x", modifiers: [.command, .shift])
            }
        }
        
        MenuBarExtra("PAT", systemImage: "brain.head.profile") {
            Button("Control Center") {
                NSApp.activate(ignoringOtherApps: true)
                // In a real app, we'd ensure the window is open
            }
            
            Divider()
            
            ForEach(manager.services) { service in
                Button("\(service.status.indicator) \(service.name)") {
                    if case .stopped = service.status {
                        manager.startService(service.id)
                    } else {
                        manager.stopService(service.id)
                    }
                }
            }
            
            Divider()
            
            Button("Quit PAT Manager") {
                manager.stopAll()
                NSApplication.shared.terminate(nil)
            }
        }
    }
}

extension ServiceStatus {
    var indicator: String {
        switch self {
        case .stopped: return "○"
        case .starting: return "◍"
        case .running: return "●"
        case .error: return "⚠"
        }
    }
}
