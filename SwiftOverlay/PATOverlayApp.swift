import SwiftUI

@main
struct PATOverlayApp: App {
    var body: some Scene {
        WindowGroup {
            EnhancedOverlayView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unifiedCompact)
        // Make window stay on top
        .commands {
            CommandGroup(after: .windowSize) {
                Button("Float on Top") {
                    NSApp.windows.first?.level = .floating
                }
            }
        }
    }
}