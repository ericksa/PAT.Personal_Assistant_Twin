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
        }
    }
}
