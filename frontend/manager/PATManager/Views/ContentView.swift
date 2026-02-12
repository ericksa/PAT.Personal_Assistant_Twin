import SwiftUI

struct ContentView: View {
    @StateObject private var manager = ProcessManager()
    @StateObject private var voice = VoiceManager()
    @State private var selectedTab = "dashboard"
    
    var body: some View {
        NavigationSplitView {
            List(selection: $selectedTab) {
                Label("Dashboard", systemImage: "speedometer")
                    .tag("dashboard")
                Label("Console Logs", systemImage: "terminal")
                    .tag("logs")
                
                Section("Quick Links") {
                    Button("Open Teleprompter") { openURL("http://localhost:8005") }
                    Button("Open n8n") { openURL("http://localhost:5678") }
                    Button("Open Grafana") { openURL("http://localhost:3000") }
                }
            }
            .navigationTitle("PAT Manager")
        } detail: {
            if selectedTab == "dashboard" {
                DashboardView()
            } else {
                LogView()
            }
        }
        .environmentObject(manager)
        .environmentObject(voice)
        .toolbar {
            ToolbarItem(placement: .status) {
                HStack {
                    StatusIndicator(isRunning: manager.services.contains { $0.status.isRunning })
                    Text(manager.services.filter { $0.status.isRunning }.count == manager.services.count ? "All Systems Active" : "Partial System Load")
                        .font(.caption)
                }
            }
            
            ToolbarItemGroup {
                Button(action: { manager.startAll() }) {
                    Label("Start All", systemImage: "play.fill")
                }
                .help("Start all services")
                
                Button(action: { manager.stopAll() }) {
                    Label("Stop All", systemImage: "stop.fill")
                }
                .help("Stop all services")
            }
        }
    }
    
    private func openURL(_ urlString: String) {
        if let url = URL(string: urlString) {
            NSWorkspace.shared.open(url)
        }
    }
}

struct StatusIndicator: View {
    let isRunning: Bool
    var body: some View {
        Circle()
            .fill(isRunning ? Color.green : Color.red)
            .frame(width: 8, height: 8)
            .shadow(color: (isRunning ? Color.green : Color.red).opacity(0.5), radius: 2)
    }
}

extension ServiceStatus {
    var isRunning: Bool {
        if case .running = self { return true }
        return false
    }
}
