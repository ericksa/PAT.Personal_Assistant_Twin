//
//  SettingsView.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import SwiftUI

struct SettingsView: View {
    @Environment(\.presentationMode) var presentationMode
    @ObservedObject var viewModel: ChatViewModel
    
    var body: some View {
        NavigationStack {
            Form {
                Section("General") {
                    Toggle("Web Search", isOn: $viewModel.useWebSearch)
                    Toggle("Memory Context", isOn: $viewModel.useMemoryContext)
                }
                
                Section("Model Selection") {
                    Picker("LLM Provider", selection: $viewModel.llmProvider) {
                        Text("Llama2").tag("llama2")
                        Text("Llama3").tag("llama3")
                        Text("Mistral").tag("mistral")
                    }
                    .pickerStyle(.menu)
                }
                
                Section("Appearance") {
                    Toggle("Dark Mode", isOn: $viewModel.useDarkMode)
                }
                
                Section("Export & Import") {
                    Button("Export as Markdown") {
                        viewModel.exportAsMarkdown()
                    }
                    Button("Import Session") {
                        // TODO: Implement import from .md or .json
                    }
                }
                
                Section("Services") {
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
                        presentationMode.wrappedValue.dismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    SettingsView(viewModel: ChatViewModel())
}

