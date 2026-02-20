import SwiftUI

/// Main content view with sidebar navigation
struct ContentView: View {
    @EnvironmentObject var manager: ProcessManager
    @EnvironmentObject var voice: VoiceManager
    @State private var selectedTab = "dashboard"
    @State private var showingSettings = false
    
    var body: some View {
        NavigationSplitView {
            sidebar
                .navigationTitle("PAT Manager")
        } detail: {
            detailContent
                .toolbar { toolbarContent }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
    }
    
    // MARK: - Subviews
    
    private var sidebar: some View {
        List(selection: $selectedTab) {
            NavigationLink(value: "dashboard") {
                Label("Dashboard", systemImage: "speedometer")
            }
            
            NavigationLink(value: "logs") {
                Label("Console Logs", systemImage: "terminal")
            }
            
            Section("Quick Links") {
                LinkButton(title: "Open Teleprompter", url: "http://localhost:8005", icon: "macwindow")
                LinkButton(title: "Open n8n", url: "http://localhost:5678", icon: "arrow.triangle.pull")
                LinkButton(title: "Open Grafana", url: "http://localhost:3000", icon: "chart.bar.fill")
            }
        }
    }
    
    @ViewBuilder
    private var detailContent: some View {
        switch selectedTab {
        case "dashboard":
            DashboardView()
        case "logs":
            LogView()
        default:
            DashboardView()
        }
    }
    
    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .status) {
            systemStatusIndicator
        }
        
        ToolbarItemGroup {
            Button(action: { manager.startAll() }) {
                Label("Start All", systemImage: "play.fill")
            }
            .help("Start all services (⌘⇧S)")
            .disabled(manager.services.allSatisfy { $0.status.isRunning })
            
            Button(action: { manager.stopAll() }) {
                Label("Stop All", systemImage: "stop.fill")
            }
            .help("Stop all services (⌘⇧X)")
            .disabled(manager.processes.isEmpty)
            
            Button(action: { showingSettings = true }) {
                Label("Settings", systemImage: "gear")
            }
            .help("Configure PAT Manager")
        }
    }
    
    private var systemStatusIndicator: some View {
        HStack(spacing: 6) {
            StatusIndicator(isRunning: manager.services.contains { $0.status.isRunning })
            Text("System Status")
                .font(.caption)
        }
    }
}

// MARK: - Helper Views

/// Status indicator showing running state
struct StatusIndicator: View {
    let isRunning: Bool
    
    var body: some View {
        Circle()
            .fill(isRunning ? Color.green : Color.red)
            .frame(width: 8, height: 8)
            .shadow(color: (isRunning ? Color.green : Color.red).opacity(0.5), radius: 2)
    }
}

/// Button that opens a URL in browser
struct LinkButton: View {
    let title: String
    let url: String
    let icon: String
    
    var body: some View {
        Button(action: {
            if let link = URL(string: url) {
                NSWorkspace.shared.open(link)
            }
        }) {
            Label(title, systemImage: icon)
        }
        .buttonStyle(.plain)
        .foregroundColor(.accentColor)
    }
}

// MARK: - Preview

#Preview {
    ContentView()
        .environmentObject(ProcessManager())
        .environmentObject(VoiceManager())
        .frame(width: 1000, height: 700)
}
