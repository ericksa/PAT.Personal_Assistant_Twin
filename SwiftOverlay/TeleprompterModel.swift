import SwiftUI
import Foundation

final class TeleprompterModel: ObservableObject {
    @Published var text: String = "Ready for your interview..."
    @Published var opacity: Double = 0.85
    @Published var fontSize: CGFloat = 24
    @Published var clickThrough: Bool = false
    @Published var windowPosition: NSRect = NSRect(x: 100, y: 200, width: 600, height: 400)
    
    // Text display properties
    @Published var textColor: NSColor = .white
    @Published var autoScroll: Bool = true
    
    // Connection status
    @Published var isConnected: Bool = false
    @Published var connectionStatus: String = "Connecting..."
    
    init() {
        // Load saved preferences
        loadPreferences()
    }
    
    private func loadPreferences() {
        let defaults = UserDefaults.standard
        
        if let savedOpacity = defaults.value(forKey: "overlayOpacity") as? Double {
            opacity = savedOpacity
        }
        if let savedFontSize = defaults.value(forKey: "overlayFontSize") as? CGFloat {
            fontSize = savedFontSize
        }
        if let savedClickThrough = defaults.value(forKey: "overlayClickThrough") as? Bool {
            clickThrough = savedClickThrough
        }
    }
    
    func savePreferences() {
        let defaults = UserDefaults.standard
        defaults.set(opacity, forKey: "overlayOpacity")
        defaults.set(fontSize, forKey: "overlayFontSize")
        defaults.set(clickThrough, forKey: "overlayClickThrough")
    }
    
    func updateConnectionStatus(_ connected: Bool, message: String? = nil) {
        isConnected = connected
        connectionStatus = message ?? (connected ? "Connected" : "Disconnected")
    }
}