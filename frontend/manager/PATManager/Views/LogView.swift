import SwiftUI

struct LogView: View {
    @EnvironmentObject var manager: ProcessManager
    @State private var filterText = ""
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Image(systemName: "terminal")
                Text("System Console")
                    .font(.headline)
                Spacer()
                TextField("Filter logs...", text: $filterText)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 200)
                Button("Clear") {
                    manager.combinedLogs = ""
                }
                .buttonStyle(.bordered)
            }
            .padding()
            .background(Color.black.opacity(0.3))
            
            ScrollViewReader { proxy in
                ScrollView {
                    Text(filteredLogs)
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(.green)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .id("logBottom")
                }
                .onChange(of: manager.combinedLogs) { _ in
                    proxy.scrollTo("logBottom", anchor: .bottom)
                }
            }
            .background(Color.black)
        }
    }
    
    var filteredLogs: String {
        if filterText.isEmpty {
            return manager.combinedLogs
        } else {
            return manager.combinedLogs.components(separatedBy: .newlines)
                .filter { $0.localizedCaseInsensitiveContains(filterText) }
                .joined(separator: "\n")
        }
    }
}
