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
    
    
    var body: some View {           // ← Add this
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
            .navigationSplitViewColumnWidth(min: 200, ideal: 250)
        } detail: {
            VStack(spacing: 0) {
                if !viewModel.areServicesHealthy() {
                    serviceStatusBanner
                }

                headerView
                messagesView

                if let errorMessage = viewModel.errorMessage {
                    errorBanner(message: errorMessage)
                }

                inputView
            }
            .navigationTitle(viewModel.currentSession?.title ?? "PAT")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    HStack(spacing: 12) {
                        // Microphone/Listening Service Status
                        Button(action: { viewModel.toggleListeningService() }) {
                            Image(systemName: viewModel.isListeningActive ? "mic.fill" : "mic.slash")
                                .foregroundColor(viewModel.listeningServiceStatusColor)
                        }
                        .buttonStyle(.borderless)
                        .help(viewModel.listeningServiceStatusText)
                        
                        // WebSocket Connection Status
                        Button(action: { viewModel.toggleWebSocketConnection() }) {
                            Image(systemName: viewModel.isWebSocketConnected ? "network" : "network.slash")
                                .foregroundColor(viewModel.webSocketStatusColor)
                        }
                        .buttonStyle(.borderless)
                        .help(viewModel.webSocketStatusText)
                        
                        // Teleprompter Status
                        Button(action: { viewModel.toggleTeleprompter() }) {
                            Image(systemName: viewModel.isTeleprompterActive ? "arrow.up.doc.fill" : "arrow.up.doc")
                                .foregroundColor(viewModel.teleprompterStatusColor)
                        }
                        .buttonStyle(.borderless)
                        .help(viewModel.teleprompterStatusText)
                        
                        // Settings
                        Button(action: { showingSettings = true }) {
                            Image(systemName: "gearshape")
                        }
                    }
                }
            }
        }
        .task {
            await viewModel.initialHealthCheck()
            loadSessions()
        }
    }
    @ViewBuilder
    private var serviceStatusBanner: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                VStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.title3)
                    
                    
                    Button("Retry") {
                        Task {
                            await viewModel.checkAllServices()
                        }
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                
                VStack(alignment: .leading, spacing: 8) {
                    Text("Services Required")
                        .font(.headline)
                    
          
                    
                    if let agentDetails = viewModel.agentHealthDetails {
                        Divider()
                        VStack(spacing: 2) {
                            Text("Service Details:")
                                .font(.caption)
                                .fontWeight(.semibold)
                            
                            HStack {
                                Text("Database: \(agentDetails.services.database)")
                                Spacer()
                                Image(systemName: agentDetails.services.database == "active" ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(agentDetails.services.database == "active" ? .green : .red)
                            }
                            .font(.caption)
                            
                            HStack {
                                Text("Redis: \(agentDetails.services.redis)")
                                Spacer()
                                Image(systemName: agentDetails.services.redis == "active" ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundColor(agentDetails.services.redis == "active" ? .green : .red)
                            }
                            .font(.caption)
                        }
                    }
                }
                
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.orange.opacity(0.1))
            
            Divider()
        }
    }
    
   
    
    @ViewBuilder
    private var headerView: some View {
        HStack {
            HStack(spacing: 6) {
                Circle()
                    .fill(viewModel.areServicesHealthy() ? .green : .red)
                    .frame(width: 8, height: 8)
                Text(viewModel.agentHealthDetails?.services.llm_provider ?? "Unknown")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            HStack(spacing: 12) {
                Button(action: { viewModel.exportAsMarkdown() }) {
                    Label("Markdown", systemImage: "doc.text")
                }
                .buttonStyle(.borderless)
                
                Button(action: { Task { await viewModel.uploadDocument() } }) {
                    Label("Upload", systemImage: "square.and.arrow.up")
                }
                .buttonStyle(.borderless)
                .disabled(viewModel.isProcessing || viewModel.ingestStatus != .healthy)
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(Color(nsColor: .controlBackgroundColor))
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
                            MessageRow(message: message)
                            
                            if message.id != viewModel.messages.last?.id {
                                Divider()
                            }
                        }
                        
                        if viewModel.isProcessing {
                            HStack(spacing: 8) {
                                ProgressView()
                                    .controlSize(.small)
                                Text("Thinking...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                        }
                    }
                }
                .onChange(of: viewModel.messages.count) { _, _ in
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
                .onChange(of: viewModel.isProcessing) { _, isProcessing in
                    if isProcessing, let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
        }
    }
    
    @ViewBuilder
    private var emptyStateView: some View {
        VStack(spacing: 20) {
            Image(systemName: "message.badge")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("Welcome to PAT")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Your Personal Assistant Twin")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if viewModel.areServicesHealthy() {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("RAG-powered document search")
                    }
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("Web search integration")
                    }
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("Local LLM support via Ollama")
                    }
                }
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.top, 20)
            } else {
                VStack(spacing: 16) {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("To start chatting, need to:")
                            .font(.headline)
                        
                        VStack(spacing: 8) {
                            stepInstruction(
                                "Start Ollama LLM service",
                                command: "ollama serve"
                            )
                            
                            stepInstruction(
                                "Download a model",
                                command: "ollama pull llama2"
                            )
                            
                            stepInstruction(
                                "Start Agent service",
                                command: "uvicorn agent.main:app --port 8002"
                            )
                            
                            stepInstruction(
                                "Check services",
                                command: "Click the 'Retry' button above"
                            )
                        }
                    }
                    .padding()
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(8)
                    .padding(.horizontal, 20)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(40)
    }
    
    @ViewBuilder
    private func stepInstruction(_ title: String, command: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "chevron.right")
                    .font(.caption2)
                    .foregroundColor(.blue)
                Text(title)
                    .font(.caption)
            }
            Text("$ \(command)")
                .foregroundColor(.secondary)
                .textSelection(.enabled)
                .padding(.leading, 16)
        }
    }
    
    @ViewBuilder
    private func errorBanner(message: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(message)
                    .font(.caption)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            
            Button(action: { viewModel.errorMessage = nil }) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(Color.orange.opacity(0.2))
    }
    
    @ViewBuilder
    private var inputView: some View {
        VStack(spacing: 12) {
            HStack(spacing: 20) {
                Toggle("Web Search", isOn: $viewModel.useWebSearch)
                    .toggleStyle(.switch)
                
                Toggle("Memory Context", isOn: $viewModel.useMemoryContext)
                    .toggleStyle(.switch)
                
                Spacer()
                
                if !viewModel.messages.isEmpty {
                    Button(action: { Task { await viewModel.regenerateLastResponse() } }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.borderless)
                    .disabled(viewModel.isProcessing || !viewModel.areServicesHealthy())
                    .help("Regenerate last response")
                }
            }
            .font(.caption)
            .padding(.horizontal, 16)
            
            Divider()
            
            HStack(spacing: 12) {
                TextField("Type your message...", text: $viewModel.inputText, axis: .vertical)
                    .focused($isInputFocused)
                    .font(.body)
                    .lineLimit(1...6) // Allow 1-6 lines
                    .textFieldStyle(.plain)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color(nsColor: .textBackgroundColor))
                    )
                
                Button(action: {
                    Task {
                        await viewModel.sendMessage()
                    }
                }) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(
                            viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !viewModel.areServicesHealthy()
                            ? .secondary
                            : .blue
                        )
                }
                .buttonStyle(.borderless)
                .disabled(
                    viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ||
                    viewModel.isProcessing ||
                    !viewModel.areServicesHealthy()
                )
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 16)
        }
        .background(Color(nsColor: .controlBackgroundColor))
    }
    
    private func loadSessions() {
        do {
            sessions = try SessionService.shared.loadAllSessions()
        } catch {
            print("Failed to load sessions: \(error)")
            viewModel.errorMessage = "Failed to load saved sessions"
        }
    }
}

#Preview {
    ChatView()
        .frame(width: 800, height: 600)
}
