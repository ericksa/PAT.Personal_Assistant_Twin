import SwiftUI

struct DashboardView: View {
    @EnvironmentObject var manager: ProcessManager
    @EnvironmentObject var voice: VoiceManager
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("System Dashboard")
                    .font(.system(size: 24, weight: .bold))
                
                HStack {
                    VStack(alignment: .leading) {
                        Text("Voice Assistant")
                            .font(.headline)
                        Text(voice.isRecording ? "Listening..." : (voice.isProcessing ? "Processing..." : "Ready"))
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    Spacer()
                    Button(action: {
                        voice.toggleRecording()
                    }) {
                        Image(systemName: voice.isRecording ? "stop.fill" : "mic.fill")
                            .font(.title)
                            .foregroundColor(.white)
                            .padding()
                            .background(voice.isRecording ? Color.red : Color.blue)
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
                .padding()
                .background(Color.white.opacity(0.05))
                .cornerRadius(12)
                
                HStack(spacing: 15) {
                    BrowserLinkCard(title: "Teleprompter", icon: "macwindow", url: "http://localhost:8005/display")
                    BrowserLinkCard(title: "Grafana", icon: "chart.bar.fill", url: "http://localhost:3000")
                    BrowserLinkCard(title: "n8n", icon: "arrow.triangle.pull", url: "http://localhost:5678")
                }
                
                Text("Services")
                    .font(.headline)
                    .padding(.top)
                
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 250))], spacing: 15) {
                    ForEach(manager.services) { service in
                        ServiceCard(service: service)
                    }
                }
            }
            .padding()
        }
    }
}

struct ServiceCard: View {
    let service: PATService
    @EnvironmentObject var manager: ProcessManager
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: service.status.iconName)
                    .foregroundColor(statusColor)
                Text(service.name)
                    .font(.headline)
                Spacer()
                if let pid = service.pid {
                    Text("PID: \(pid)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Text(service.description)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
            
            HStack {
                Button(action: {
                    if case .stopped = service.status {
                        manager.startService(service.id)
                    } else {
                        manager.stopService(service.id)
                    }
                }) {
                    Text(buttonText)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(buttonColor)
            }
        }
        .padding()
        .background(Color.white.opacity(0.05))
        .cornerRadius(10)
    }
    
    var statusColor: Color {
        switch service.status {
        case .stopped: return .gray
        case .starting: return .yellow
        case .running: return .green
        case .error: return .red
        }
    }
    
    var buttonText: String {
        switch service.status {
        case .stopped, .error: return "Start"
        default: return "Stop"
        }
    }
    
    var buttonColor: Color {
        switch service.status {
        case .stopped, .error: return .blue
        default: return .red
        }
    }
}

struct BrowserLinkCard: View {
    let title: String
    let icon: String
    let url: String
    
    var body: some View {
        Button(action: {
            if let link = URL(string: url) {
                NSWorkspace.shared.open(link)
            }
        }) {
            VStack {
                Image(systemName: icon)
                    .font(.title2)
                Text(title)
                    .font(.caption)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color.blue.opacity(0.1))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}
