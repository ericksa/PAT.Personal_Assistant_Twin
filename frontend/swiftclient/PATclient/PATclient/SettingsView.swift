import SwiftUI

struct SettingsView: View {
    @ObservedObject var viewModel: ChatViewModel
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Appearance") {
                    Toggle("Dark Mode", isOn: Binding(
                        get: { viewModel.useDarkMode },
                        set: { newValue in
                            viewModel.useDarkMode = newValue
                            viewModel.saveSessionSettings()
                            #if os(macOS)
                            // Apply theme change immediately
                            NSApp.appearance = newValue ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
                            #endif
                        }
                    ))
                }
                
                Section("Model Configuration") {
                    Picker("LLM Provider", selection: Binding(
                        get: { viewModel.llmProvider },
                        set: { newValue in
                            viewModel.llmProvider = newValue
                            viewModel.saveSessionSettings()
                        }
                    )) {
                        Text("Ollama").tag("ollama")
                        // Add other providers if supported by your backend
                    }
                    
                    Picker("Model", selection: Binding(
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
                                ProgressView().controlSize(.small)
                            }
                        }
                    }
                }
            }
            .formStyle(.grouped)
            .navigationTitle("Settings")
            #if os(macOS)
            .frame(width: 400, height: 450)
            #endif
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

