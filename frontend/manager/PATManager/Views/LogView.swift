import SwiftUI

/// Console log view with filtering and export
struct LogView: View {
    @EnvironmentObject var manager: ProcessManager
    @State private var filterText = ""
    @State private var selectedLevel: ProcessManager.LogLevel?
    @State private var autoScroll = true
    @State private var showingExportConfirmation = false
    @State private var exportedURL: URL?
    
    private let levels = ProcessManager.LogLevel.allCases
    
    var body: some View {
        VStack(spacing: 0) {
            toolbar
            logContent
        }
        .alert("Export Complete", isPresented: $showingExportConfirmation) {
            Button("OK") {}
            if let url = exportedURL {
                Button("Show in Finder") {
                    NSWorkspace.shared.selectFile(url.path, inFileViewerRootedAtPath: "")
                }
            }
        } message: {
            if let url = exportedURL {
                Text("Logs exported to:\n\(url.path)")
            }
        }
    }
    
    // MARK: - Subviews
    
    private var toolbar: some View {
        HStack(spacing: 12) {
            Image(systemName: "terminal")
                .foregroundColor(.green)
            
            Text("System Console")
                .font(.headline)
            
            Spacer()
            
            // Log level filter
            Picker("Level", selection: $selectedLevel) {
                Text("All")
                    .tag(nil as ProcessManager.LogLevel?)
                ForEach(levels, id: \.self) { level in
                    Text(level.rawValue)
                        .tag(level as ProcessManager.LogLevel?)
                }
            }
            .pickerStyle(.segmented)
            .frame(width: 300)
            
            // Search filter
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                TextField("Filter logs...", text: $filterText)
                    .textFieldStyle(.plain)
                    .frame(width: 150)
            }
            .padding(6)
            .background(Color.gray.opacity(0.2))
            .cornerRadius(6)
            
            Divider()
                .frame(height: 20)
            
            // Auto-scroll toggle
            Toggle("Auto-scroll", isOn: $autoScroll)
                .toggleStyle(.switch)
                .controlSize(.small)
            
            Divider()
                .frame(height: 20)
            
            // Action buttons
            Button(action: exportLogs) {
                Label("Export", systemImage: "square.and.arrow.up")
            }
            .buttonStyle(.bordered)
            .help("Export logs to file")
            
            Button(action: { manager.clearLogs() }) {
                Label("Clear", systemImage: "trash")
            }
            .buttonStyle(.bordered)
            .tint(.red)
            .help("Clear all logs")
        }
        .padding()
        .background(Color.black.opacity(0.5))
    }
    
    private var logContent: some View {
        ScrollViewReader { proxy in
            ScrollView {
                Text(filteredLogs)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(.green)
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .id("logBottom")
                    .textSelection(.enabled)
            }
            .background(Color.black)
            .onChange(of: manager.combinedLogs) { _, _ in
                if autoScroll {
                    DispatchQueue.main.async {
                        withAnimation(.easeOut(duration: 0.1)) {
                            proxy.scrollTo("logBottom", anchor: .bottom)
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Computed Properties
    
    private var filteredLogs: String {
        var lines = manager.combinedLogs.components(separatedBy: .newlines)
        
        // Filter by level
        if let level = selectedLevel {
            lines = lines.filter { $0.contains("[\(level.rawValue)]") }
        }
        
        // Filter by search text
        if !filterText.isEmpty {
            lines = lines.filter { $0.localizedCaseInsensitiveContains(filterText) }
        }
        
        return lines.joined(separator: "\n")
    }
    
    // MARK: - Actions
    
    private func exportLogs() {
        if let url = manager.exportLogs() {
            exportedURL = url
            showingExportConfirmation = true
        }
    }
}



#Preview {
    LogView()
        .environmentObject(ProcessManager())
        .frame(width: 900, height: 500)
}
