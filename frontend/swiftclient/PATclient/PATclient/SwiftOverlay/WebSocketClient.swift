import Foundation
import Combine

class WebSocketClient: ObservableObject {
    static let shared = WebSocketClient()
    
    @Published var currentText = ""
    @Published var isConnected = false
    
    private var cancellables = Set<AnyCancellable>()
    private var webSocketTask: URLSessionWebSocketTask?
    private let url = URL(string: "ws://localhost:8765")!
    
    init() {
        connect()
    }
    
    func connect() {
        guard let url = URL(string: "ws://localhost:8765") else {
            print("❌ Invalid WebSocket URL")
            return
        }
        
        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        
        print("🌐 WebSocket client connecting...")
        
        // Start receiving messages
        receiveMessage()
        
        // Send initial connection message
        let connectMessage = ["type": "connection", "client": "PATOverlay"]
        sendMessage(connectMessage)
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
        print("🌐 WebSocket client disconnected")
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleIncomingMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleIncomingMessage(text)
                    }
                @unknown default:
                    break
                }
                
                // Continue receiving
                self?.receiveMessage()
                
            case .failure(let error):
                print("❌ WebSocket receive error: \(error)")
                self?.isConnected = false
                
                // Attempt reconnection after delay
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    self?.connect()
                }
            }
        }
    }
    
    private func handleIncomingMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            print("❌ Failed to parse WebSocket message: \(text)")
            return
        }
        
        guard let type = json["type"] as? String else {
            print("❌ Unknown message type: \(text)")
            return
        }
        
        switch type {
        case "transcription":
            if let transcription = json["text"] as? String {
                DispatchQueue.main.async { [weak self] in
                    self?.currentText = transcription
                    print("📄 Received transcription: \(transcription)")
                }
            }
            
        case "system":
            if let message = json["message"] as? String {
                if message == "Connected to PAT Teleprompter" {
                    DispatchQueue.main.async { [weak self] in
                        self?.isConnected = true
                        print("✅ WebSocket client connected successfully!")
                    }
                }
            }
            
        default:
            print("📨 Unknown message type: \(type)")
        }
    }
    
    func sendMessage(_ message: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: message),
              let jsonString = String(data: data, encoding: .utf8) else {
            print("❌ Failed to encode message")
            return
        }
        
        webSocketTask?.send(.string(jsonString)) { error in
            if let error = error {
                print("❌ WebSocket send error: \(error)")
            } else {
                print("📤 Sent message: \(message)")
            }
        }
    }
    
    deinit {
        disconnect()
    }
}

// Example usage in SwiftUI view:
struct TeleprompterView: View {
    @StateObject private var webSocketClient = WebSocketClient.shared
    
    var body: some View {
        VStack {
            // Connection status indicator
            HStack {
                Circle()
                    .fill(webSocketClient.isConnected ? .green : .red)
                    .frame(width: 10, height: 10)
                Text(webSocketClient.isConnected ? "Connected" : "Disconnected")
                    .font(.caption)
            }
            
            // Display current transcription
            ScrollView {
                Text(webSocketClient.currentText)
                    .font(.title2)
                    .multilineTextAlignment(.center)
                    .padding()
            }
        }
        .onAppear {
            WebSocketClient.shared.connect()
        }
        .onDisappear {
            WebSocketClient.shared.disconnect()
        }
    }
}