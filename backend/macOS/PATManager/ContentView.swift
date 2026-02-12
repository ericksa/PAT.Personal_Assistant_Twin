import SwiftUI

struct ContentView: View {
    @StateObject private var runner = ServiceRunner()
    @State private var testOutput = ""
    @State private var isRunningTests = false
    
    var body: some View {
        VStack(spacing: 20) {
            Text("PAT Backend Manager")
                .font(.largeTitle)
                .padding(.top)
            
            HStack(spacing: 40) {
                // API Control
                VStack {
                    Text("PAT Core API")
                        .font(.headline)
                    
                    Circle()
                        .fill(runner.isApiRunning ? Color.green : Color.red)
                        .frame(width: 20, height: 20)
                        .overlay(Circle().stroke(Color.white, lineWidth: 2))
                        .shadow(radius: 2)
                    
                    Button(action: {
                        runner.toggleApi()
                    }) {
                        Text(runner.isApiRunning ? "Stop API" : "Start API")
                            .frame(width: 100)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(runner.isApiRunning ? .red : .blue)
                }
                
                // Sync Worker Control
                VStack {
                    Text("Sync Worker")
                        .font(.headline)
                    
                    Circle()
                        .fill(runner.isSyncWorkerRunning ? Color.green : Color.red)
                        .frame(width: 20, height: 20)
                        .overlay(Circle().stroke(Color.white, lineWidth: 2))
                        .shadow(radius: 2)
                    
                    Button(action: {
                        runner.toggleSyncWorker()
                    }) {
                        Text(runner.isSyncWorkerRunning ? "Stop Sync" : "Start Sync")
                            .frame(width: 100)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(runner.isSyncWorkerRunning ? .red : .blue)
                }
            }
            .padding()
            .background(Color.white.opacity(0.05))
            .cornerRadius(12)
            
            Divider()
            
            // Testing Section
            VStack(alignment: .leading) {
                HStack {
                    Text("System Health & Tests")
                        .font(.headline)
                    Spacer()
                    if isRunningTests {
                        ProgressView().scaleEffect(0.5)
                    }
                    Button("Run Diagnostic Tests") {
                        isRunningTests = true
                        runner.runTests { output in
                            testOutput = output
                            isRunningTests = false
                        }
                    }
                    .disabled(isRunningTests)
                }
                
                ScrollView {
                    Text(testOutput.isEmpty ? "No test results yet." : testOutput)
                        .font(.system(.body, design: .monospaced))
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(height: 150)
                .background(Color.black)
                .cornerRadius(8)
            }
            .padding(.horizontal)
            
            // Logs Section
            TabView {
                LogView(title: "API Logs", logs: runner.apiLogs)
                    .tabItem { Text("API") }
                
                LogView(title: "Sync Logs", logs: runner.syncWorkerLogs)
                    .tabItem { Text("Sync") }
            }
            .frame(height: 250)
        }
        .frame(width: 600, height: 700)
    }
}

struct LogView: View {
    let title: String
    let logs: String
    
    var body: some View {
        VStack(alignment: .leading) {
            ScrollViewReader { proxy in
                ScrollView {
                    Text(logs.isEmpty ? "Waiting for logs..." : logs)
                        .font(.system(size: 11, design: .monospaced))
                        .padding(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .id("bottom")
                }
                .onChange(of: logs) { _ in
                    proxy.scrollTo("bottom", anchor: .bottom)
                }
            }
        }
        .background(Color.black.opacity(0.8))
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
