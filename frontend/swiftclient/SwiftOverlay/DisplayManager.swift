import Cocoa

final class DisplayManager {
    static let shared = DisplayManager()
    
    private init() {}
    
    var screens: [NSScreen] {
        NSScreen.screens
    }
    
    var primaryScreen: NSScreen? {
        NSScreen.main
    }
    
    func getAvailableScreens() -> [String: NSScreen] {
        var screenMap: [String: NSScreen] = [:]
        
        for screen in screens {
            let screenNumber = screen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] ?? "unknown"
            let displayID = "Display_\(screenNumber)"
            screenMap[displayID] = screen
        }
        
        return screenMap
    }
    
    func moveWindowToScreen(window: NSWindow, screenID: String) {
        let screenMap = getAvailableScreens()
        guard let targetScreen = screenMap[screenID] else { return }
        
        var windowFrame = window.frame
        
        // Center window on target screen
        windowFrame.origin.x = targetScreen.visibleFrame.midX - windowFrame.width / 2
        windowFrame.origin.y = targetScreen.visibleFrame.midY - windowFrame.height / 2
        
        // Ensure window stays within screen bounds
        windowFrame = ensureFrameIsOnScreen(windowFrame, screen: targetScreen)
        
        window.setFrame(windowFrame, display: true)
    }
    
    func moveWindowToNextScreen(window: NSWindow) {
        let allScreens = screens
        guard allScreens.count > 1 else { return }
        
        let currentScreen = window.screen ?? NSScreen.main ?? allScreens.first!
        guard let currentIndex = allScreens.firstIndex(of: currentScreen) else { return }
        
        let nextIndex = (currentIndex + 1) % allScreens.count
        let nextScreen = allScreens[nextIndex]
        
        let nextScreenNumber = nextScreen.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] ?? "unknown"
        moveWindowToScreen(window: window, screenID: "Display_\(nextScreenNumber)")
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