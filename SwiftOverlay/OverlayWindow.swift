import AppKit
import SwiftUI

final class OverlayWindow: NSWindow {
    @Published var teleprompterModel = TeleprompterModel()
    
    override var canBecomeKey: Bool { true }
    
    init() {
        // Create window with initial size
        let rect = NSRect(x: 100, y: 200, width: 600, height: 400)
        super.init(
            contentRect: rect,
            styleMask: [.borderless, .resizable],
            backing: .buffered,
            defer: false
        )
        
        // Configure window properties
        level = .floating  // Always on top of other windows
        isOpaque = false
        backgroundColor = .clear
        alphaValue = 0.85  // Default transparency
        isMovableByWindowBackground = true  // Drag anywhere
        ignoresMouseEvents = false  // Initially interactable
        isReleasedWhenClosed = false
        
        // Set default title
        title = "PAT Teleprompter Overlay"
        
        // Add SwiftUI content
        setupContentView()
    }
    
    private func setupContentView() {
        let contentView = EnhancedOverlayView()
            .environmentObject(teleprompterModel)
        let hostingView = NSHostingView(rootView: contentView)
        hostingView.frame = self.contentRect(forFrameRect: frame)
        hostingView.autoresizingMask = [.width, .height]
        
        // Set content view
        self.contentView = hostingView
    }
    
    func setClickThrough(_ enabled: Bool) {
        ignoresMouseEvents = enabled
    }
    
    func setTransparency(_ value: Double) {
        alphaValue = max(0.1, min(1.0, value))
    }
    
    func maximizeWindow() {
        if let screen = self.screen {
            setFrame(screen.visibleFrame, display: true)
        }
    }
    
    func restoreWindow() {
        // Restore to default size
        setFrame(NSRect(x: 100, y: 200, width: 600, height: 400), display: true)
    }
    
    override func mouseDown(with event: NSEvent) {
        super.mouseDown(with: event)
        // Dragging handled automatically by isMovableByWindowBackground
    }
}