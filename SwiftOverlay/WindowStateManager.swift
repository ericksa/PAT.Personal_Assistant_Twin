import Cocoa
import Foundation

final class WindowStateManager {
    static let shared = WindowStateManager()
    
    private let userDefaults = UserDefaults.standard
    private let windowPositionKey = "overlayWindowPosition"
    
    private init() {}
    
    func saveWindowPosition(for window: OverlayWindow) {
        let screenInfo = getScreenInfo(for: window)
        let positionData: [String: Any] = [
            "frame": [
                "x": window.frame.origin.x,
                "y": window.frame.origin.y,
                "width": window.frame.size.width,
                "height": window.frame.size.height
            ],
            "screen": screenInfo
        ]
        
        userDefaults.set(positionData, forKey: windowPositionKey)
    }
    
    func restoreWindowPosition(for window: OverlayWindow) {
        guard let positionData = userDefaults.dictionary(forKey: windowPositionKey),
              let frameDict = positionData["frame"] as? [String: CGFloat],
              let screenInfo = positionData["screen"] as? [String: Any],
              let x = frameDict["x"],
              let y = frameDict["y"],
              let width = frameDict["width"],
              let height = frameDict["height"] else {
            // Set default position
            if let primaryScreen = NSScreen.main {
                let frame = NSRect(x: primaryScreen.visibleFrame.midX - 300,
                                  y: primaryScreen.visibleFrame.midY - 200,
                                  width: 600, height: 400)
                window.setFrame(frame, display: true)
            }
            return
        }
        
        // Check if screen still exists
        let screenID = screenInfo["id"] as? UInt32
        let foundScreen = NSScreen.screens.first { screen in
            screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? UInt32 == screenID
        }
        
        if let targetScreen = foundScreen {
            // Adjust frame to ensure it's on the screen
            var adjustedFrame = NSRect(x: x, y: y, width: width, height: height)
            adjustedFrame = ensureFrameIsOnScreen(adjustedFrame, screen: targetScreen)
            window.setFrame(adjustedFrame, display: true)
        } else {
            // Screen not found, use primary screen
            if let primaryScreen = NSScreen.main {
                let frame = NSRect(x: primaryScreen.visibleFrame.midX - 300,
                                  y: primaryScreen.visibleFrame.midY - 200,
                                  width: 600, height: 400)
                window.setFrame(frame, display: true)
            }
        }
    }
    
    private func getScreenInfo(for window: NSWindow) -> [String: Any] {
        guard let screen = window.screen else {
            return ["id": 0 as UInt32]
        }
        
        let screenID = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? UInt32 ?? 0
        return ["id": screenID as UInt32]
    }
    
    private func ensureFrameIsOnScreen(_ frame: NSRect, screen: NSScreen) -> NSRect {
        var adjustedFrame = frame
        let screenFrame = screen.visibleFrame
        
        // Ensure frame is within screen bounds
        if adjustedFrame.maxX > screenFrame.maxX {
            adjustedFrame.origin.x = screenFrame.maxX - adjustedFrame.width
        }
        if adjustedFrame.maxY > screenFrame.maxY {
            adjustedFrame.origin.y = screenFrame.maxY - adjustedFrame.height
        }
        if adjustedFrame.minX < screenFrame.minX {
            adjustedFrame.origin.x = screenFrame.minX
        }
        if adjustedFrame.minY < screenFrame.minY {
            adjustedFrame.origin.y = screenFrame.minY
        }
        
        return adjustedFrame
    }
}