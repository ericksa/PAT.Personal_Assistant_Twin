//
//  PATclientApp.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import SwiftUI

@main
struct PATclientApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 900, minHeight: 600)
        }
        .windowStyle(.titleBar)
        .windowResizability(.contentSize)
        .defaultSize(width: 1200, height: 800)
        .commands {
            PATCommands()
        }

        // Settings window
        Settings {
            EnhancedSettingsView()
        }
    }
}

// MARK: - Menu Commands
struct PATCommands: Commands {
    var body: some Commands {
        // Replace standard new window command
        CommandGroup(replacing: .newItem) {
            Button("New Chat") {
                NotificationCenter.default.post(name: .newChatRequested, object: nil)
            }
            .keyboardShortcut("n", modifiers: .command)

            Divider()

            Button("New Window") {
                openNewWindow()
            }
            .keyboardShortcut("n", modifiers: [.command, .shift])
        }

        // Edit menu commands
        CommandMenu("Conversation") {
            Button("Clear Messages") {
                NotificationCenter.default.post(name: .clearMessagesRequested, object: nil)
            }
            .keyboardShortcut("k", modifiers: [.command, .shift])

            Button("Export Conversation...") {
                NotificationCenter.default.post(name: .exportConversationRequested, object: nil)
            }
            .keyboardShortcut("e", modifiers: .command)

            Divider()

            Button("Refresh Models") {
                NotificationCenter.default.post(name: .refreshModelsRequested, object: nil)
            }
            .keyboardShortcut("r", modifiers: .command)
        }

        // View menu commands
        CommandMenu("View") {
            Toggle("Sidebar", isOn: .constant(true))
                .keyboardShortcut("s", modifiers: [.command, .control])

            Divider()

            Menu("Appearance") {
                Button("Light") {
                    NSApp.appearance = NSAppearance(named: .aqua)
                }

                Button("Dark") {
                    NSApp.appearance = NSAppearance(named: .darkAqua)
                }

                Button("System") {
                    NSApp.appearance = nil
                }
            }
        }
    }

    private func openNewWindow() {
        let newWindow = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1200, height: 800),
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        newWindow.title = "PAT Client"
        newWindow.contentView = NSHostingView(rootView: ContentView())
        newWindow.makeKeyAndOrderFront(nil)
    }
}

// Notification names for menu commands
extension Notification.Name {
    static let newChatRequested = Notification.Name("newChatRequested")
    static let clearMessagesRequested = Notification.Name("clearMessagesRequested")
    static let exportConversationRequested = Notification.Name("exportConversationRequested")
    static let refreshModelsRequested = Notification.Name("refreshModelsRequested")
}
