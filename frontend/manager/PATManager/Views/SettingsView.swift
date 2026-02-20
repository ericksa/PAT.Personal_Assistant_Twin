import SwiftUI

/// Settings view for configuring PAT Manager
struct SettingsView: View {
    @EnvironmentObject var manager: ProcessManager
    @Environment(\.dismiss) var dismiss
    
    @State private var backendPath: String = ""
    @State private var pythonPath: String = ""
    @State private var enableHealthChecks: Bool = true
    @State private var healthCheckInterval: Double = 30
    @State private var showingPathPicker = false
    @State private var pathType: PathType?
    
    enum PathType {
        case backend, python
    }
    
    var body: some View {
        Form {
            Section("Paths") {
                HStack {
                    TextField("Backend Path", text: $backendPath)
                        .textFieldStyle(.roundedBorder)
                    Button("Browse...") {
                        pathType = .backend
                        showingPathPicker = true
                    }
                }
                
                HStack {
                    TextField("Python Path", text: $pythonPath)
                        .textFieldStyle(.roundedBorder)
                    Button("Browse...") {
                        pathType = .python
                        showingPathPicker = true
                    }
                }
            }
            
            Section("Health Checks") {
                Toggle("Enable Health Checks", isOn: $enableHealthChecks)
                
                if enableHealthChecks {
                    VStack(alignment: .leading) {
                        Text("Check Interval: \(Int(healthCheckInterval)) seconds")
                        Slider(value: $healthCheckInterval, in: 5...300, step: 5)
                    }
                }
            }
            
            Section {
                HStack {
                    Spacer()
                    Button("Reset to Defaults") {
                        resetToDefaults()
                    }
                    .buttonStyle(.bordered)
                    
                    Button("Save") {
                        saveSettings()
                    }
                    .buttonStyle(.borderedProminent)
                    Spacer()
                }
            }
        }
        .formStyle(.grouped)
        .padding()
        .frame(width: 500, height: 300)
        .onAppear {
            loadCurrentSettings()
        }
        .fileImporter(
            isPresented: $showingPathPicker,
            allowedContentTypes: pathType == .python ? [.executable, .unixExecutable] : [.directory],
            allowsMultipleSelection: false
        ) { result in
            handlePathSelection(result)
        }
    }
    
    private func loadCurrentSettings() {
        backendPath = manager.configuration.backendPath
        pythonPath = manager.configuration.pythonPath
        enableHealthChecks = manager.configuration.enableHealthChecks
        healthCheckInterval = manager.configuration.healthCheckInterval
    }
    
    private func saveSettings() {
        manager.configuration.backendPath = backendPath
        manager.configuration.pythonPath = pythonPath
        manager.configuration.enableHealthChecks = enableHealthChecks
        manager.configuration.healthCheckInterval = healthCheckInterval
        manager.saveConfiguration()
        dismiss()
    }
    
    private func resetToDefaults() {
        let defaults = ProcessManagerConfiguration.default
        backendPath = defaults.backendPath
        pythonPath = defaults.pythonPath
        enableHealthChecks = defaults.enableHealthChecks
        healthCheckInterval = defaults.healthCheckInterval
    }
    
    private func handlePathSelection(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else { return }
            switch pathType {
            case .backend:
                backendPath = url.path
            case .python:
                pythonPath = url.path
            case .none:
                break
            }
        case .failure(let error):
            print("Path selection failed: \(error)")
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(ProcessManager())
}
