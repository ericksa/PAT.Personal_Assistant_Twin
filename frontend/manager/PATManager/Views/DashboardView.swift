import SwiftUI

/// Dashboard showing service status and quick actions
struct DashboardView: View {
    @EnvironmentObject var manager: ProcessManager
    @EnvironmentObject var voice: VoiceManager
    @State private var showingVoiceError = false
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                headerSection
                voiceAssistantSection
                quickLinksSection
                servicesSection
            }
            .padding()
        }
        .alert("Voice Error", isPresented: $showingVoiceError) {
            Button("OK") {}
            Button("Open Settings") {
                NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone")!)
            }
        } message: {
            if let error = voice.lastError {
                Text(error.localizedDescription)
            } else {
                Text("An unknown error occurred")
            }
        }
        .onChange(of: voice.lastError) { _, newError in
            showingVoiceError = newError != nil
        }
    }
    
    // MARK: - Sections
    
    private var headerSection: some View {
        HStack {
            Text("System Dashboard")
                .font(.system(size: 28, weight: .bold))
            
            Spacer()
            
            if manager.isHealthChecking {
                HStack(spacing: 4) {
                    Image(systemName: "heart.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                    Text("Health checks active")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    private var voiceAssistantSection: some View {
        HStack(spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Voice Assistant")
                    .font(.headline)
                
                HStack(spacing: 6) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 6, height: 6)
                    Text(statusText)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
                
                if voice.isProcessing {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .scaleEffect(0.6)
                        .padding(.top, 4)
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 8) {
                Button(action: {
                    voice.toggleRecording()
                }) {
                    Image(systemName: voice.isRecording ? "stop.fill" : "mic.fill")
                        .font(.title2)
                        .foregroundColor(.white)
                        .frame(width: 56, height: 56)
                        .background(voice.isRecording ? Color.red : Color.accentColor)
                        .clipShape(Circle())
                        .shadow(radius: 2)
                }
                .buttonStyle(.plain)
                .help(voice.isRecording ? "Stop recording" : "Start recording")
                
                if !voice.transcript.isEmpty {
                    Text("\"\(voice.transcript)\"")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                        .frame(maxWidth: 200, alignment: .trailing)
                }
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.1))
        .cornerRadius(12)
    }
    
    private var quickLinksSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick Links")
                .font(.headline)
            
            HStack(spacing: 12) {
                BrowserLinkCard(
                    title: "Teleprompter",
                    icon: "macwindow",
                    url: "http://localhost:8005/display"
                )
                BrowserLinkCard(
                    title: "Grafana",
                    icon: "chart.bar.fill",
                    url: "http://localhost:3000"
                )
                BrowserLinkCard(
                    title: "n8n",
                    icon: "arrow.triangle.pull",
                    url: "http://localhost:5678"
                )
            }
        }
    }
    
    private var servicesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Services")
                    .font(.headline)
                
                Spacer()
                
                Text("\(manager.services.filter { $0.status.isRunning }.count)/\(manager.services.count) running")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 280))], spacing: 12) {
                ForEach(manager.services) { service in
                    ServiceCard(service: service)
                }
            }
        }
    }
    
    // MARK: - Helpers
    
    private var statusText: String {
        if voice.isRecording {
            return "Listening..."
        } else if voice.isProcessing {
            return "Processing..."
        } else if let error = voice.lastError {
            return "Error: \(error.localizedDescription.prefix(30))..."
        } else {
            return "Ready"
        }
    }
    
    private var statusColor: Color {
        if voice.isRecording {
            return .red
        } else if voice.isProcessing {
            return .yellow
        } else if voice.lastError != nil {
            return .orange
        } else {
            return .green
        }
    }
}

// MARK: - Service Card

/// Card displaying a single service's status and controls
struct ServiceCard: View {
    let service: PATService
    @EnvironmentObject var manager: ProcessManager
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                statusIcon
                
                Text(service.name)
                    .font(.headline)
                
                Spacer()
                
                if let pid = service.pid {
                    Text("PID: \(pid)")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            Text(service.description)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
            
            if let port = service.port {
                HStack {
                    Image(systemName: "network")
                        .font(.caption2)
                    Text(":\(port)")
                        .font(.caption2)
                        .monospaced()
                }
                .foregroundColor(.secondary)
            }
            
            if case .running(let health) = service.status {
                HStack {
                    Circle()
                        .fill(healthColor(health))
                        .frame(width: 6, height: 6)
                    Text(healthText(health))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            HStack {
                Button(action: {
                    if case .stopped = service.status {
                        manager.startService(service.id)
                    } else {
                        manager.stopService(service.id)
                    }
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: buttonIcon)
                        Text(buttonText)
                    }
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(buttonColor)
                .disabled(service.status == .starting)
            }
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(10)
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(statusBorderColor, lineWidth: 1)
        )
    }
    
    private var statusIcon: some View {
        Image(systemName: service.status.iconName)
            .foregroundColor(statusColor)
            .font(.title3)
    }
    
    private var statusColor: Color {
        switch service.status {
        case .stopped: return .gray
        case .starting: return .yellow
        case .running(let health):
            switch health {
            case .healthy: return .green
            case .unhealthy: return .orange
            case .unknown: return .blue
            }
        case .error: return .red
        }
    }
    
    private var statusBorderColor: Color {
        switch service.status {
        case .running(.healthy): return .green.opacity(0.3)
        case .running(.unhealthy): return .orange.opacity(0.3)
        case .error: return .red.opacity(0.3)
        default: return .clear
        }
    }
    
    private var buttonText: String {
        switch service.status {
        case .stopped: return "Start"
        case .starting: return "Starting..."
        case .running: return "Stop"
        case .error: return "Retry"
        }
    }
    
    private var buttonIcon: String {
        switch service.status {
        case .stopped, .error: return "play.fill"
        case .starting: return "arrow.clockwise"
        case .running: return "stop.fill"
        }
    }
    
    private var buttonColor: Color {
        switch service.status {
        case .stopped, .error: return .blue
        case .starting: return .gray
        case .running: return .red
        }
    }
    
    private func healthColor(_ health: ServiceHealth) -> Color {
        switch health {
        case .healthy: return .green
        case .unhealthy: return .orange
        case .unknown: return .gray
        }
    }
    
    private func healthText(_ health: ServiceHealth) -> String {
        switch health {
        case .healthy: return "Healthy"
        case .unhealthy(let reason): return "Unhealthy: \(reason)"
        case .unknown: return "Health unknown"
        }
    }
}

// MARK: - Browser Link Card

/// Card for opening external tools in browser
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
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(.accentColor)
                Text(title)
                    .font(.caption)
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(Color.accentColor.opacity(0.1))
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    DashboardView()
        .environmentObject(ProcessManager())
        .environmentObject(VoiceManager())
        .frame(width: 800, height: 600)
}
