// PATOverlayApp.swift - Main application entry point
import SwiftUI

class PATOverlayAppDelegate: NSObject, NSApplicationDelegate {
    var overlayWindow: OverlayWindow?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create the floating overlay window
        overlayWindow = OverlayWindow()
        overlayWindow?.makeKeyAndOrderFront(nil)
        
        // Load saved window position
        if let window = overlayWindow {
            WindowStateManager.shared.restoreWindowPosition(for: window)
        }
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        // Save window position before quitting
        if let window = overlayWindow {
            WindowStateManager.shared.saveWindowPosition(for: window)
        }
    }
    
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return false
    }
}

@main
struct PATOverlayApp: App {
    @NSApplicationDelegateAdaptor(PATOverlayAppDelegate.self) var appDelegate
    var body: some Scene {
        WindowGroup { EmptyView() }
    }
}