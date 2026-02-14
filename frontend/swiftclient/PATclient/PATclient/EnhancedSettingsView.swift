//
//  EnhancedSettingsView.swift
//  PATclient
//
//  Enhanced Settings View with macOS-appropriate organization
//

import SwiftUI

struct EnhancedSettingsView: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var selectedTab = SettingsTab.general

    enum SettingsTab: String, CaseIterable, Identifiable {
        case general = "General"
        case models = "Models"
        case appearance = "Appearance"
        case advanced = "Advanced"

        var id: String { rawValue }

        var icon: String {
            switch self {
            case .general: return "gear"
            case .models: return "cpu"
            case .appearance: return "paintpalette"
            case .advanced: return "wrench.and.screwdriver"
            }
        }
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            GeneralSettings(viewModel: viewModel)
                .tabItem {
                    Label(SettingsTab.general.rawValue, systemImage: SettingsTab.general.icon)
                }
                .tag(SettingsTab.general)

            ModelSettings(viewModel: viewModel)
                .tabItem {
                    Label(SettingsTab.models.rawValue, systemImage: SettingsTab.models.icon)
                }
                .tag(SettingsTab.models)

            AppearanceSettings(viewModel: viewModel)
                .tabItem {
                    Label(SettingsTab.appearance.rawValue, systemImage: SettingsTab.appearance.icon)
                }
                .tag(SettingsTab.appearance)

            AdvancedSettings(viewModel: viewModel)
                .tabItem {
                    Label(SettingsTab.advanced.rawValue, systemImage: SettingsTab.advanced.icon)
                }
                .tag(SettingsTab.advanced)
        }
        .frame(width: 500, height: 400)
        .padding()
    }
}

// MARK: - General Settings
struct GeneralSettings: View {
    @ObservedObject var viewModel: ChatViewModel
    @AppStorage("startupBehavior") private var startupBehavior = StartupBehavior.showLastSession
    @AppStorage("autoSaveInterval") private var autoSaveInterval = 30

    enum StartupBehavior: String, CaseIterable {
        case showLastSession = "Show Last Session"
        case showWelcome = "Show Welcome Screen"
        case createNew = "Create New Chat"
    }

    var body: some View {
        Form {
            Section {
                Picker("On Startup:", selection: $startupBehavior) {
                    ForEach(StartupBehavior.allCases, id: \.self) { behavior in
                        Text(behavior.rawValue).tag(behavior)
                    }
                }

                Picker("Auto-save Interval:", selection: $autoSaveInterval) {
                    Text("30 seconds").tag(30)
                    Text("1 minute").tag(60)
                    Text("5 minutes").tag(300)
                    Text("Never").tag(0)
                }

                Toggle("Show Notifications", isOn: .constant(true))
                Toggle("Play Sound Effects", isOn: .constant(false))
            } header: {
                Text("General")
                    .font(.headline)
            }

            Section {
                Toggle("Start at Login", isOn: .constant(false))
                    .disabled(true) // Placeholder

                Toggle("Show in Dock", isOn: .constant(true))
                Toggle("Show in Menu Bar", isOn: .constant(false))
                    .disabled(true) // Placeholder
            } header: {
                Text("System Integration")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
    }
}

// MARK: - Model Settings
struct ModelSettings: View {
    @ObservedObject var viewModel: ChatViewModel

    var body: some View {
        Form {
            Section {
                Picker("Provider:", selection: Binding(
                    get: { viewModel.llmProvider },
                    set: { newValue in
                        viewModel.llmProvider = newValue
                        viewModel.saveSessionSettings()
                    }
                )) {
                    Text("Ollama").tag("ollama")
                    Text("Local MLX").tag("mlx")
                }

                Picker("Default Model:", selection: Binding(
                    get: { viewModel.selectedModel },
                    set: { newValue in
                        viewModel.selectedModel = newValue
                        viewModel.saveSessionSettings()
                    }
                )) {
                    if viewModel.availableModels.isEmpty {
                        Text("No models available").tag(viewModel.selectedModel)
                    } else {
                        ForEach(viewModel.availableModels, id: \.self) { model in
                            Text(model).tag(model)
                        }
                    }
                }

                Button(action: {
                    Task {
                        await viewModel.refreshAvailableModels()
                    }
                }) {
                    HStack {
                        Text("Refresh Available Models")
                        if viewModel.isRefreshingModels {
                            Spacer()
                            ProgressView()
                                .controlSize(.small)
                                .scaleEffect(0.8)
                        }
                    }
                }
            } header: {
                Text("Model Configuration")
                    .font(.headline)
            }

            Section {
                HStack {
                    Text("Context Window:")
                    Spacer()
                    Text("4,096 tokens")
                        .foregroundColor(.secondary)
                }

                HStack {
                    Text("Max Tokens:")
                    Spacer()
                    Text("2,048")
                        .foregroundColor(.secondary)
                }

                Toggle("Stream Responses", isOn: .constant(true))
            } header: {
                Text("Inference Settings")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
    }
}

// MARK: - Appearance Settings
struct AppearanceSettings: View {
    @ObservedObject var viewModel: ChatViewModel
    @AppStorage("accentColor") private var accentColor = AccentColor.blue
    @AppStorage("messageSpacing") private var messageSpacing: Double = 12
    @AppStorage("codeTheme") private var codeTheme = CodeTheme.github

    enum AccentColor: String, CaseIterable {
        case blue = "Blue"
        case purple = "Purple"
        case green = "Green"
        case orange = "Orange"
        case pink = "Pink"

        var color: Color {
            switch self {
            case .blue: return .blue
            case .purple: return .purple
            case .green: return .green
            case .orange: return .orange
            case .pink: return .pink
            }
        }
    }

    enum CodeTheme: String, CaseIterable {
        case github = "GitHub"
        case monokai = "Monokai"
        case solarized = "Solarized"
        case dracula = "Dracula"
    }

    var body: some View {
        Form {
            Section {
                Picker("Accent Color:", selection: $accentColor) {
                    ForEach(AccentColor.allCases, id: \.self) { color in
                        HStack {
                            Circle()
                                .fill(color.color)
                                .frame(width: 12, height: 12)
                            Text(color.rawValue)
                        }
                        .tag(color)
                    }
                }

                Toggle("Use System Appearance", isOn: Binding(
                    get: { viewModel.useDarkMode == nil },
                    set: { isSystem in
                        viewModel.useDarkMode = isSystem ? nil : false
                        viewModel.saveSessionSettings()
                        applyAppearance()
                    }
                ))

                if viewModel.useDarkMode != nil {
                    Toggle("Dark Mode", isOn: Binding(
                        get: { viewModel.useDarkMode ?? false },
                        set: { newValue in
                            viewModel.useDarkMode = newValue
                            viewModel.saveSessionSettings()
                            applyAppearance()
                        }
                    ))
                }
            } header: {
                Text("Theme")
                    .font(.headline)
            }

            Section {
                Picker("Code Theme:", selection: $codeTheme) {
                    ForEach(CodeTheme.allCases, id: \.self) { theme in
                        Text(theme.rawValue).tag(theme)
                    }
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Message Spacing:")
                    Slider(value: $messageSpacing, in: 4...24, step: 2) {
                        Text("\(Int(messageSpacing)) pt")
                    }
                }

                Toggle("Show Timestamps", isOn: .constant(false))
                Toggle("Show Avatars", isOn: .constant(true))
                Toggle("Compact Mode", isOn: .constant(false))
            } header: {
                Text("Chat Display")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
    }

    private func applyAppearance() {
        #if os(macOS)
        if let useDarkMode = viewModel.useDarkMode {
            NSApp.appearance = useDarkMode ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
        } else {
            NSApp.appearance = nil
        }
        #endif
    }
}

// MARK: - Advanced Settings
struct AdvancedSettings: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var showingResetConfirmation = false
    @AppStorage("logLevel") private var logLevel = LogLevel.info

    enum LogLevel: String, CaseIterable {
        case debug = "Debug"
        case info = "Info"
        case warning = "Warning"
        case error = "Error"
    }

    var body: some View {
        Form {
            Section {
                Picker("Log Level:", selection: $logLevel) {
                    ForEach(LogLevel.allCases, id: \.self) { level in
                        Text(level.rawValue).tag(level)
                    }
                }

                Button("Open Logs Folder") {
                    openLogsFolder()
                }

                Button("Clear All Conversations...") {
                    showingResetConfirmation = true
                }
                .foregroundColor(.red)
            } header: {
                Text("Debugging")
                    .font(.headline)
            }

            Section {
                HStack {
                    Text("Version:")
                    Spacer()
                    Text("1.0.0 (Build 2024.02.13)")
                        .foregroundColor(.secondary)
                }

                Button("Check for Updates...") {
                    // Placeholder
                }
                .disabled(true)

                Button("View Documentation") {
                    if let url = URL(string: "https://github.com/adamerickson/PAT") {
                        NSWorkspace.shared.open(url)
                    }
                }
            } header: {
                Text("About")
                    .font(.headline)
            }
        }
        .formStyle(.grouped)
        .alert("Clear All Conversations?", isPresented: $showingResetConfirmation) {
            Button("Cancel", role: .cancel) { }
            Button("Clear All", role: .destructive) {
                Task {
                    await viewModel.deleteAllSessions()
                }
            }
        } message: {
            Text("This action cannot be undone. All conversation history will be permanently deleted.")
        }
    }

    private func openLogsFolder() {
        let fileManager = FileManager.default
        if let appSupport = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first {
            let logsURL = appSupport.appendingPathComponent("PAT/Logs")
            NSWorkspace.shared.open(logsURL)
        }
    }
}
