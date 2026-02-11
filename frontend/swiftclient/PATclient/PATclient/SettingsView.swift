import SwiftUI
import Combine
import os.log

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.colorScheme) private var colorScheme
    
    var body: some View {
        NavigationStack {
            Form {
                Section("General") {
                    Toggle("Web Search", isOn: $viewModel.useWebSearch)
                    Toggle("Memory Context", isOn: $viewModel.useMemoryContext)
                }
                
                Section("Model Selection") {
                    Picker("LLM Provider", selection: $viewModel.llmProvider) {
                        Text("Local Ollama").tag("ollama")
                        Text("Llama 2").tag("llama2")
                        Text("Llama 3").tag("llama3")
                        Text("Mistral").tag("mistral")
                    }
                    .pickerStyle(.menu)
                    .onChange(of: viewModel.llmProvider) { _, _ in
                        Task {
                            await viewModel.refreshAvailableModels()
                        }
                    }
                    
                    if !viewModel.availableModels.isEmpty {
                        Picker("Model", selection: $viewModel.selectedModel) {
                            ForEach(viewModel.availableModels, id: \.self) { model in
                                Text(model).tag(model)
                            }
                        }
                        .pickerStyle(.menu)
                        .disabled(viewModel.availableModels.isEmpty)
                    }
                    
                    Button("Refresh Models") {
                        Task {
                            await viewModel.refreshAvailableModels()
                        }
                    }
                    
                    if viewModel.isRefreshingModels {
                        ProgressView("Loading models...")
                            .progressViewStyle(CircularProgressViewStyle())
                    }
                }
                
                Section("Appearance") {
                    Toggle("Dark Mode", isOn: Binding(
                        get: { viewModel.useDarkMode },
                        set: { newValue in
                            viewModel.useDarkMode = newValue
                            viewModel.saveSessionSettings()
                            // Apply theme change immediately
                            NSApp.appearance = newValue ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
                        }
                    ))
                }
                
                Section("Documents") {
                    Button("Upload Document") {
                        Task {
                            await viewModel.uploadDocument()
                        }
                    }
                    
                    Button("Manage Documents") {
                        // TODO: Implement document management
                    }
                }
                
                Section("Export & Import") {
                    Button("Export as Markdown") {
                        viewModel.exportAsMarkdown()
                    }
                    
                    Button("Import Session") {
                        importSession()
                    }
                    
                    Button("Delete Current Session") {
                        deleteCurrentSession()
                    }
                }
                
                Section("Services") {
                    VStack(alignment: .leading, spacing: 8) {
                        statusRow("Ollama Service", viewModel.ollamaStatus)
                        statusRow("Agent Service", viewModel.agentStatus)
                    }
                    
                    Button("Check Health Again") {
                        Task {
                            await viewModel.checkAllServices()
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    @ViewBuilder
    private func statusRow(_ title: String, _ status: ServiceStatus) -> some View {
        HStack {
            Text(title)
            Spacer()
            Circle()
                .fill(status.color)
                .frame(width: 8, height: 8)
            Text(status.displayText)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    private func importSession() {
        // Implement file picker for JSON import
        print("Import session functionality not yet implemented")
    }
    
    private func deleteCurrentSession() {
        guard let session = viewModel.currentSession else { return }
        
        do {
            try SessionService.shared.deleteSession(id: session.id)
            viewModel.startNewSession()
        } catch {
            print("Failed to delete session: \(error)")
        }
    }
}

#Preview {
    SettingsView(viewModel: ChatViewModel())
}

