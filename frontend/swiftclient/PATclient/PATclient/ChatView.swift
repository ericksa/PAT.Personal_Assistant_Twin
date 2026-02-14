//
//  ChatView.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import SwiftUI

struct ChatView: View {

    @StateObject private var viewModel = ChatViewModel()
    @State private var showingSettings = false
    @State private var sessions: [ChatSession] = []
    @FocusState private var isInputFocused: Bool
    @Environment(\.colorScheme) private var colorScheme

    private var isDarkMode: Bool { colorScheme == .dark }

    var body: some View {
        NavigationSplitView {
            SessionListView(
                sessions: $sessions,
                selectedSession: Binding(
                    get: { viewModel.currentSession ?? ChatSession(id: UUID(), title: "New Session", messages: []) },
                    set: { viewModel.currentSession = $0 }
                ),
                onCreateNew: { viewModel.startNewSession() },
                onSelectSession: { viewModel.loadSession($0) },
                onDeleteSession: {
                    do {
                        try SessionService.shared.deleteSession(id: $0.id)
                        loadSessions()
                    } catch {
                        viewModel.errorMessage = "Failed to delete session"
                    }
                }
            )
            .nativeSidebar()
            .navigationSplitViewColumnWidth(min: 220, ideal: 260)
        } detail: {
            VStack(spacing: 0) {
                // Service status indicator at top
                ServiceStatusIndicator(viewModel: viewModel)

                messagesView

                if let errorMessage = viewModel.errorMessage {
                    errorBanner(message: errorMessage)
                }

                Divider()

                inputView
            }
            .background(Color(nsColor: .windowBackgroundColor))
            .navigationTitle(viewModel.currentSession?.title ?? "PAT")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    HStack(spacing: 8) {
                        // LLM Provider selector
                        Menu {
                            ForEach(LLMProvider.allCases) { provider in
                                Button(action: {
                                    viewModel.llmProvider = provider.rawValue
                                    Task { await viewModel.checkAllServices() }
                                }) {
                                    HStack {
                                        Image(systemName: provider.icon)
                                        Text(provider.displayName)
                                        if viewModel.llmProvider == provider.rawValue {
                                            Image(systemName: "checkmark")
                                        }
                                    }
                                }
                            }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: getProviderIcon(for: viewModel.llmProvider))
                                    .font(.caption)
                                Text(getProviderName(for: viewModel.llmProvider))
                                    .font(.caption)
                            }
                            .foregroundColor(.secondary)
                        }
                        .menuStyle(.borderlessButton)
                        .help("Select LLM Provider")

                        Divider()
                            .frame(height: 16)

                        Button(action: { viewModel.toggleListeningService() }) {
                            Image(systemName: "ear")
                                .foregroundColor(viewModel.isListeningActive ? .green : .secondary)
                        }
                        .buttonStyle(.borderless)
                        .help("Toggle Listening Service")

                        Button(action: { launchTeleprompter() }) {
                            Image(systemName: "rectangle.and.pencil.and.ellipsis")
                        }
                        .buttonStyle(.borderless)
                        .help("Launch Teleprompter")

                        Button(action: { showingSettings = true }) {
                            Image(systemName: "gearshape")
                        }
                        .buttonStyle(.borderless)
                        .help("Settings")
                    }
                }
            }
            .task {
                await viewModel.initialHealthCheck()
                await loadSessionsAsync()
                await viewModel.refreshAvailableModels()
            }
            .onDisappear {
                viewModel.stopListeningService()
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView(viewModel: viewModel)
                    .frame(minWidth: 500, minHeight: 400)
            }
        }
    }

    private func getProviderIcon(for provider: String) -> String {
        LLMProvider(rawValue: provider)?.icon ?? "cpu"
    }

    private func getProviderName(for provider: String) -> String {
        LLMProvider(rawValue: provider)?.displayName ?? provider.capitalized
    }

    @ViewBuilder
    private var messagesView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 0) {
                    if viewModel.messages.isEmpty {
                        emptyStateView
                    } else {
                        ForEach(viewModel.messages) { message in
                            MessageRow(message: message, viewModel: viewModel)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)

                            if message.id != viewModel.messages.last?.id {
                                Divider()
                                    .padding(.horizontal, 16)
                            }
                        }

                        if viewModel.isProcessing {
                            HStack(spacing: 12) {
                                ProgressView()
                                    .controlSize(.small)
                                    .scaleEffect(0.8)

                                Text("PAT is thinking...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.vertical, 16)
                            .padding(.horizontal, 16)
                        }
                    }
                }
                .padding(.vertical, 16)
                .onChange(of: viewModel.messages.count) { _, _ in
                    if let lastMessage = viewModel.messages.last {
                        withAnimation(.easeOut(duration: 0.2)) {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
                .onChange(of: viewModel.isProcessing) { _, isProcessing in
                    if isProcessing, let lastMessage = viewModel.messages.last {
                        withAnimation(.easeOut(duration: 0.2)) {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var emptyStateView: some View {
        VStack(spacing: 24) {
            Spacer()

            // App icon placeholder
            ZStack {
                RoundedRectangle(cornerRadius: 24)
                    .fill(
                        LinearGradient(
                            colors: [.blue.opacity(0.3), .purple.opacity(0.3)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 100, height: 100)
                    .overlay(
                        RoundedRectangle(cornerRadius: 24)
                            .stroke(Color.secondary.opacity(0.2), lineWidth: 1)
                    )

                Image(systemName: "person.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(.primary)
            }

            VStack(spacing: 8) {
                Text("Welcome to PAT")
                    .font(.largeTitle)
                    .fontWeight(.semibold)

                Text("Your Personal Assistant Twin")
                    .font(.title3)
                    .foregroundColor(.secondary)
            }

            if viewModel.areServicesHealthy() {
                // Feature grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    FeatureCard(
                        icon: "doc.text.magnifyingglass",
                        title: "RAG Search",
                        description: "Search your documents"
                    )

                    FeatureCard(
                        icon: "globe",
                        title: "Web Search",
                        description: "Search the web"
                    )

                    FeatureCard(
                        icon: "calendar.badge.clock",
                        title: "Calendar",
                        description: "Manage events"
                    )

                    FeatureCard(
                        icon: "checklist",
                        title: "Tasks",
                        description: "Track todos"
                    )
                }
                .frame(maxWidth: 400)
                .padding(.top, 20)
            } else {
                VStack(spacing: 16) {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("To start chatting:")
                            .font(.headline)

                        VStack(spacing: 8) {
                            StepItem(
                                number: 1,
                                title: "Start PAT Core",
                                command: "python -m backend.pat_core"
                            )

                            StepItem(
                                number: 2,
                                title: "Start Agent Service",
                                command: "uvicorn backend.agent.main:app --port 8002"
                            )

                            StepItem(
                                number: 3,
                                title: "Start LM Studio",
                                command: "Load GLM-4.6v-flash model"
                            )
                        }
                    }
                    .padding()
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(12)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
                    )
                    .padding(.horizontal, 40)
                    .padding(.top, 20)
                }
            }

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }

    @ViewBuilder
    private func errorBanner(message: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
                .font(.title3)

            VStack(alignment: .leading, spacing: 4) {
                Text(message)
                    .font(.subheadline)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            Spacer()

            Button(action: { viewModel.errorMessage = nil }) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.orange.opacity(0.1))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
        )
        .padding(.horizontal, 16)
        .padding(.bottom, 8)
    }

    @ViewBuilder
    private var inputView: some View {
        VStack(spacing: 0) {
            // Tool toggles bar
            HStack(spacing: 16) {
                Toggle(isOn: $viewModel.useWebSearch) {
                    Label("Web Search", systemImage: "globe")
                }
                .toggleStyle(.checkbox)
                .controlSize(.small)

                Toggle(isOn: $viewModel.useMemoryContext) {
                    Label("Memory", systemImage: "brain.head.profile")
                }
                .toggleStyle(.checkbox)
                .controlSize(.small)

                Spacer()

                // Model selector
                if !viewModel.availableModels.isEmpty {
                    Picker("Model", selection: $viewModel.selectedModel) {
                        ForEach(viewModel.availableModels, id: \.self) { model in
                            Text(model).tag(model)
                        }
                    }
                    .pickerStyle(.menu)
                    .controlSize(.small)
                    .frame(width: 150)
                }

                if !viewModel.messages.isEmpty {
                    Button(action: { Task { await viewModel.regenerateLastResponse() } }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.borderless)
                    .disabled(viewModel.isProcessing || !viewModel.areServicesHealthy())
                    .help("Regenerate last response")
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color(nsColor: .controlBackgroundColor))

            Divider()

            // Input field
            HStack(spacing: 12) {
                // Attachment menu
                Menu {
                    Button(action: {
                        Task { await viewModel.uploadDocument() }
                    }) {
                        Label("Upload Document", systemImage: "doc")
                    }

                    Divider()

                    Button(action: {
                        Task { await viewModel.uploadResume() }
                    }) {
                        Label("Upload Resume", systemImage: "person.crop.rectangle")
                    }
                } label: {
                    Image(systemName: "paperclip")
                        .font(.title3)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.borderless)
                .help("Attach files")

                TextField("Message PAT...", text: $viewModel.inputText, axis: .vertical)
                    .focused($isInputFocused)
                    .font(.body)
                    .lineLimit(1...6)
                    .textFieldStyle(.plain)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color(nsColor: .textBackgroundColor))
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 20)
                            .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                    )

                Button(action: {
                    Task {
                        await viewModel.sendMessage()
                    }
                }) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                        .foregroundStyle(
                            viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !viewModel.areServicesHealthy()
                            ? Color.secondary
                            : Color.accentColor
                        )
                }
                .buttonStyle(.borderless)
                .disabled(
                    viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                    viewModel.isProcessing ||
                    !viewModel.areServicesHealthy()
                )
                .keyboardShortcut(.return, modifiers: .command)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private func loadSessions() {
        do {
            sessions = try SessionService.shared.loadAllSessions()
        } catch {
            print("Failed to load sessions: \(error)")
            viewModel.errorMessage = "Failed to load saved sessions"
        }
    }

    private func loadSessionsAsync() async {
        DispatchQueue.main.async {
            do {
                self.sessions = try SessionService.shared.loadAllSessions()
            } catch {
                print("Failed to load sessions: \(error)")
                self.viewModel.errorMessage = "Failed to load saved sessions"
            }
        }
    }

    private func launchTeleprompter() {
        // Use the standalone teleprompter app that handles overlay + listening service integration
        let teleprompterURL = URL(fileURLWithPath: "../PATTeleprompter.app")

        if FileManager.default.fileExists(atPath: teleprompterURL.path) {
            // Launch standalone teleprompter app
            _ = NSWorkspace.shared.openApplication(at: teleprompterURL, configuration: NSWorkspace.OpenConfiguration())

            viewModel.errorMessage = "🎬 PATTEL Teleprompter launched!"
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                self.viewModel.errorMessage = nil
            }

            return
        } else {
            // Fallback to old method if standalone app not found
            startListeningService()

            let overlayURL = URL(fileURLWithPath: "/Users/adamerickson/Projects/PAT/frontend/swiftclient/SwiftOverlayExported/PATOverlay.app")
            if FileManager.default.fileExists(atPath: overlayURL.path) {
                let appConfiguration = NSWorkspace.OpenConfiguration()
                appConfiguration.activates = true

                _ = NSWorkspace.shared.open(overlayURL, configuration: appConfiguration)

                viewModel.errorMessage = "🔄 Overlay launched successfully"
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    self.viewModel.errorMessage = nil
                }

                return
            }

            viewModel.errorMessage = "❌ Teleprompter components not found"
        }
    }

    private func startListeningService() {
        // Use shell command to start the Python listening service
        let scriptPath = "/Users/adamerickson/Projects/PAT/backend/services/listening/live_interview_listener.py"

        guard FileManager.default.fileExists(atPath: scriptPath) else {
            viewModel.errorMessage = "Listening service not found at: \(scriptPath)"
            return
        }

        let task = Process()
        task.launchPath = "/usr/bin/env"
        task.arguments = ["python3", scriptPath]

        do {
            task.launch()
            DispatchQueue.main.async {
                viewModel.errorMessage = "🔄 Listening service started"
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    self.viewModel.errorMessage = nil
                }
            }
        } catch {
            viewModel.errorMessage = "❌ Failed to start listening service: \(error.localizedDescription)"
        }
    }
}

// MARK: - Feature Card
struct FeatureCard: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.accentColor)

            VStack(spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)

                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 16)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.secondary.opacity(0.05))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
        )
    }
}

// MARK: - Step Item
struct StepItem: View {
    let number: Int
    let title: String
    let command: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.accentColor.opacity(0.1))
                    .frame(width: 24, height: 24)
                Text("\(number)")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.accentColor)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Text(command)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .fontDesign(.monospaced)
                    .textSelection(.enabled)
            }
        }
    }
}

#Preview {
    ChatView()
        .frame(width: 900, height: 700)
}
