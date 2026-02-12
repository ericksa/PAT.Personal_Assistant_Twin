//
//  AppDelegate.swift
//  PATclient
//
//  Created by Adam Erickson on 2/11/26.
//

import Cocoa

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        // Stop the listening service before terminating
        Task { @MainActor in
            // Access the shared ChatViewModel and stop listening service
            // Since ChatViewModel is @StateObject in ChatView, we need to find an alternative
            // The best approach is to emit a notification that ChatView can listen to
            NotificationCenter.default.post(name: .appWillTerminate, object: nil)
        }
        return .terminateNow
    }
}

extension Notification.Name {
    static let appWillTerminate = Notification.Name("appWillTerminate")
}