import SwiftUI
import Foundation

class WebSocketManager: NSObject, ObservableObject {
    @Published var isConnected = false
    @Published var latestMessage = "Connecting to PAT service..."

    private var webSocketTask: URLSessionWebSocketTask?
    private let urlString = "ws://localhost:8005/ws"

    override init() {
        super.init()
        connect()
    }

    func connect() {
        guard let url = URL(string: urlString) else {
            latestMessage = "Invalid WebSocket URL"
            return
        }

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.delegate = self
        webSocketTask?.resume()

        listen()
    }

    private func listen() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    if let data = text.data(using: .utf8),
                       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let content = json["content"] as? String {
                        DispatchQueue.main.async {
                            self?.latestMessage = content
                        }
                    } else {
                        DispatchQueue.main.async {
                            self?.latestMessage = text
                        }
                    }
                case .data(_):
                    DispatchQueue.main.async {
                        self?.latestMessage = "Binary data received"
                    }
                @unknown default:
                    break
                }
                self?.listen() // Continue listening
            case .failure(let error):
                DispatchQueue.main.async {
                    self?.latestMessage = "WebSocket error: \(error.localizedDescription)"
                    self?.isConnected = false
                }
            }
        }
    }

    func sendMessage(_ message: String) {
        guard let webSocketTask = webSocketTask else { return }

        webSocketTask.send(URLSessionWebSocketTask.Message.string(message)) { error in
            if let error = error {
                print("Error sending message: \(error)")
            }
        }
    }

    func sendPing() {
        sendMessage("ping")
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        DispatchQueue.main.async {
            self.isConnected = false
            self.latestMessage = "Disconnected from PAT service"
        }
    }
}

extension WebSocketManager: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        DispatchQueue.main.async {
            self.isConnected = true
            self.latestMessage = "Connected to PAT service"
        }
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        DispatchQueue.main.async {
            self.isConnected = false
            self.latestMessage = "Disconnected from PAT service"
        }
    }
}