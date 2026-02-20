import SwiftUI

/// Main app entry point for PAT Manager
@main
struct PATManagerApp: App {
    @StateObject private var manager = ProcessManager()
    @StateObject private var voice = VoiceManager()
    @AppStorage("showMenuBarExtra") private var showMenuBarExtra = true
    
    var body: some Scene {
        // Main window
        WindowGroup {
            ContentView()
                .frame(minWidth: 900, minHeight: 600)
                .environmentObject(manager)
                .environmentObject(voice)
        }
        .commands {
            appCommands
        }
        
        // Menu bar extra
        MenuBarExtra("PAT Manager", systemImage: "brain.head.profile", isInserted: $showMenuBarExtra) {
            MenuBarContent()
                .environmentObject(manager)
        }
    }
    
    // MARK: - Commands
    
    private var appCommands: some Commands {
        Group {
            CommandGroup(replacing: .appInfo) {
                Button("About PAT Manager") {
                    showAboutWindow()
                }
            }
            
            CommandGroup(replacing: .newItem) {
                Button("Start All Services") {
                    manager.startAll()
                }
                .keyboardShortcut("s", modifiers: [.command, .shift])
                
                Button("Stop All Services") {
                    manager.stopAll()
                }
                .keyboardShortcut("x", modifiers: [.command, .shift])
                
                Divider()
                
                Button("Toggle Voice Recording") {
                    voice.toggleRecording()
                }
                .keyboardShortcut("r", modifiers: [.command, .option])
            }
            
            CommandMenu("View") {
                Toggle("Show Menu Bar Icon", isOn: $showMenuBarExtra)
                    .keyboardShortcut("m", modifiers: [.command, .option])
            }
        }
    }
    
    // MARK: - Helpers
    
    private func showAboutWindow() {
        let alert = NSAlert()
        alert.messageText = "PAT Manager"
        alert.informativeText = """
            Version 1.0
            
            Personal Assistant Technology
            Service management and control center.
            
            © 2024 PAT Team
            """
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
}

// MARK: - Menu Bar Content

/// Menu bar extra content showing service status
struct MenuBarContent: View {
    @EnvironmentObject var manager: ProcessManager
    @Environment(\.openWindow) var openWindow
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack {
                Image(systemName: "brain.head.profile")
                    .foregroundColor(.accentColor)
                Text("PAT Manager")
                    .font(.headline)
            }
            .padding()
            
            Divider()
            
            // Quick actions
            Button("Open Control Center") {
                NSApp.activate(ignoringOtherApps: true)
                openWindow(id: "main")
            }
            
            Divider()
            
            // Service list
            ScrollView {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(manager.services) { service in
                        ServiceMenuItem(service: service)
                    }
                }
                .padding(.horizontal)
            }
            .frame(maxHeight: 200)
            
            Divider()
            
            // Global actions
            HStack {
                Button("Start All") {
                    manager.startAll()
                }
                .disabled(manager.services.allSatisfy { $0.status.isRunning })
                
                Button("Stop All") {
                    manager.stopAll()
                }
                .disabled(manager.processes.isEmpty)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
            
            Divider()
            
            Button("Quit PAT Manager") {
                manager.stopAll()
                NSApplication.shared.terminate(nil)
            }
            .padding()
        }
        .frame(width: 240)
    }
}

// MARK: - Service Menu Item

/// Individual service row in menu bar
struct ServiceMenuItem: View {
    let service: PATService
    @EnvironmentObject var manager: ProcessManager
    
    var body: some View {
        Button(action: {
            if case .stopped = service.status {
                manager.startService(service.id)
            } else {
                manager.stopService(service.id)
            }
        }) {
            HStack {
                Text(service.status.indicator)
                    .font(.system(size: 10))
                Text(service.name)
                    .font(.system(size: 13))
                Spacer()
                
                if case .running = service.status {
                    Image(systemName: "stop.fill")
                        .font(.caption)
                        .foregroundColor(.red)
                } else {
                    Image(systemName: "play.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                }
            }
        }
        .buttonStyle(.plain)
        .padding(.vertical, 2)
        .foregroundColor(textColor)
        .disabled(service.status == .starting)
    }
    
    private var textColor: Color {
        switch service.status {
        case .stopped: return .secondary
        case .starting: return .yellow
        case .running: return .primary
        case .error: return .red
        }
    }
}


