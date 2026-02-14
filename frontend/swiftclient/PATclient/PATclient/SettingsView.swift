import SwiftUI

struct SettingsView: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var selectedTab = 0

    var body: some View {
        NavigationStack {
            TabView(selection: $selectedTab) {
                // General Tab
                generalTab
                    .tabItem {
                        Label("General", systemImage: "gear")
                    }
                    .tag(0)

                // LLM Tab
                llmTab
                    .tabItem {
                        Label("LLM", systemImage: "cpu")
                    }
                    .tag(1)

                // Services Tab
                servicesTab
                    .tabItem {
                        Label("Services", systemImage: "network")
                    }
                    .tag(2)

                // Advanced Tab
                advancedTab
                    .tabItem {
                        Label("Advanced", systemImage: "slider.horizontal.3")
                    }
                    .tag(3)
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                    .keyboardShortcut(.escape, modifiers: [])
                }
            }
        }
        .frame(minWidth: 600, minHeight: 450)
    }

    // MARK: - General Tab
    private var generalTab: some View {
        Form {
            Section {
                HStack {
                    Image(systemName: "person.fill")
                        .font(.title2)
                        .foregroundColor(.accentColor)
                        .frame(width: 40, height: 40)
                        .background(Color.accentColor.opacity(0.1))
                        .cornerRadius(8)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("PAT Client")
                            .font(.headline)
                        Text("Version 1.0")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 8)
            }

            Section("Appearance") {
                Toggle("Dark Mode", isOn: Binding(
                    get: { viewModel.useDarkMode },
                    set: { newValue in
                        viewModel.useDarkMode = newValue
                        viewModel.saveSessionSettings()
                        #if os(macOS)
                        NSApp.appearance = newValue ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
                        #endif
                    }
                ))

                Toggle("Translucent Sidebar", isOn: .constant(true))
                    .disabled(true)
                    .help("Always enabled for native macOS look")
            }

            Section("Behavior") {
                Toggle("Auto-save Sessions", isOn: .constant(true))
                Toggle("Show Keyboard Shortcuts", isOn: .constant(true))
            }
        }
        .formStyle(.grouped)
    }

    // MARK: - LLM Tab
    private var llmTab: some View {
        Form {
            Section("Provider") {
                Picker("LLM Provider", selection: Binding(
                    get: { viewModel.llmProvider },
                    set: { newValue in
                        viewModel.llmProvider = newValue
                        Task { await viewModel.refreshAvailableModels() }
                        viewModel.saveSessionSettings()
                    }
                )) {
                    ForEach(LLMProvider.allCases) { provider in
                        Label(provider.displayName, systemImage: provider.icon)
                            .tag(provider.rawValue)
                    }
                }
                .pickerStyle(.radioGroup)

                // Provider description
                Group {
                    if viewModel.llmProvider == "lmstudio" {
                        Text("Uses LM Studio's OpenAI-compatible API at localhost:1234")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    } else {
                        Text("Uses Ollama API at localhost:11434")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }

            Section("Model") {
                Picker("Model", selection: Binding(
                    get: { viewModel.selectedModel },
                    set: { newValue in
                        viewModel.selectedModel = newValue
                        viewModel.saveSessionSettings()
                    }
                )) {
                    if viewModel.availableModels.isEmpty {
                        if viewModel.llmProvider == "lmstudio" {
                            Text("GLM-4.6v-flash (Default)").tag("GLM-4.6v-flash")
                        } else {
                            Text("No models available").tag(viewModel.selectedModel)
                        }
                    } else {
                        ForEach(Array(viewModel.availableModels.enumerated()), id: \.offset) { index, model in
                            Text(model).tag(model)
                        }
                    }
                }
                .pickerStyle(.menu)

                HStack {
                    Button(action: {
                        Task {
                            await viewModel.refreshAvailableModels()
                        }
                    }) {
                        HStack {
                            Image(systemName: "arrow.clockwise")
                            Text("Refresh Models")
                        }
                    }
                    .disabled(viewModel.isRefreshingModels)

                    Spacer()

                    if viewModel.isRefreshingModels {
                        ProgressView()
                            .controlSize(.small)
                    }
                }
                .padding(.vertical, 4)

                // Current status
                HStack {
                    Text("Status:")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Circle()
                        .fill(viewModel.llmProvider == "lmstudio" ? viewModel.lmStudioStatus.color : viewModel.ollamaStatus.color)
                        .frame(width: 8, height: 8)
                    Text(viewModel.llmProvider == "lmstudio" ? viewModel.lmStudioStatus.displayText : viewModel.ollamaStatus.displayText)
                        .font(.caption)
                        .foregroundColor(viewModel.llmProvider == "lmstudio" ? viewModel.lmStudioStatus.color : viewModel.ollamaStatus.color)
                }
            }

            if viewModel.llmProvider == "lmstudio" {
                Section("LM Studio Configuration") {
                    HStack {
                        Text("Endpoint:")
                            .font(.subheadline)
                        Spacer()
                        Text(Config.lmStudioBaseURL)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .textSelection(.enabled)
                    }

                    HStack {
                        Text("Default Model:")
                            .font(.subheadline)
                        Spacer()
                        Text("GLM-4.6v-flash")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .formStyle(.grouped)
    }

    // MARK: - Services Tab
    private var servicesTab: some View {
        Form {
            Section("Service Status") {
                ServiceStatusRow(
                    name: "PAT Core",
                    icon: "desktopcomputer",
                    status: viewModel.patCoreStatus,
                    endpoint: Config.patCoreBaseURL
                )

                ServiceStatusRow(
                    name: "Agent",
                    icon: "bubble.left.and.bubble.right",
                    status: viewModel.agentStatus,
                    endpoint: Config.agentBaseURL
                )

                ServiceStatusRow(
                    name: "Ingest",
                    icon: "arrow.up.arrow.down",
                    status: viewModel.ingestStatus,
                    endpoint: Config.ingestBaseURL
                )

                ServiceStatusRow(
                    name: "LLM (Ollama)",
                    icon: "cpu",
                    status: viewModel.ollamaStatus,
                    endpoint: Config.ollamaBaseURL
                )

                ServiceStatusRow(
                    name: "LLM (LM Studio)",
                    icon: "desktopcomputer",
                    status: viewModel.lmStudioStatus,
                    endpoint: Config.lmStudioBaseURL
                )
            }

            Section("Actions") {
                Button(action: {
                    Task { await viewModel.checkAllServices() }
                }) {
                    Label("Check All Services", systemImage: "arrow.clockwise")
                }

                Button(action: {
                    viewModel.startListeningService()
                }) {
                    Label("Start Listening Service", systemImage: "ear")
                }
                .disabled(viewModel.isListeningActive)

                Button(action: {
                    viewModel.stopListeningService()
                }) {
                    Label("Stop Listening Service", systemImage: "ear.slash")
                }
                .disabled(!viewModel.isListeningActive)
            }
        }
        .formStyle(.grouped)
    }

    // MARK: - Advanced Tab
    private var advancedTab: some View {
        Form {
            Section("Chat") {
                Toggle("Web Search", isOn: Binding(
                    get: { viewModel.useWebSearch },
                    set: { newValue in
                        viewModel.useWebSearch = newValue
                        viewModel.saveSessionSettings()
                    }
                ))

                Toggle("Memory Context", isOn: Binding(
                    get: { viewModel.useMemoryContext },
                    set: { newValue in
                        viewModel.useMemoryContext = newValue
                        viewModel.saveSessionSettings()
                    }
                ))
            }

            Section("Session Management") {
                Button(action: { viewModel.exportAsMarkdown() }) {
                    Label("Export as Markdown", systemImage: "doc.text")
                }

                Button(action: { viewModel.exportAsJSON() }) {
                    Label("Export as JSON", systemImage: "doc.text.fill")
                }

                Divider()

                Button(action: { viewModel.clearMessages() }) {
                    Label("Clear Current Session", systemImage: "trash")
                }
                .foregroundColor(.red)
            }

            Section("Debug") {
                Button(action: {
                    Task { await viewModel.checkAllServices() }
                }) {
                    Label("Run Health Check", systemImage: "stethoscope")
                }
            }
        }
        .formStyle(.grouped)
    }
}

// MARK: - Service Status Row
struct ServiceStatusRow: View {
    let name: String
    let icon: String
    let status: ServiceStatus
    let endpoint: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundColor(status.color)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(name)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Text(endpoint)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(1)
            }

            Spacer()

            HStack(spacing: 6) {
                Circle()
                    .fill(status.color)
                    .frame(width: 8, height: 8)
                Text(status.displayText)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(status.color)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    SettingsView(viewModel: ChatViewModel())
}
