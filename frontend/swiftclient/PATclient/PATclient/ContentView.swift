//
//  ContentView.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import SwiftUI

struct ContentView: View {
    @State private var selectedTab = 0
    @StateObject private var chatViewModel = ChatViewModel()
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "bubble.left.and.bubble.right")
                }
                .tag(0)
            
            CalendarView()
                .tabItem {
                    Label("Calendar", systemImage: "calendar")
                }
                .tag(1)
            
            EmailsView()
                .tabItem {
                    Label("Emails", systemImage: "envelope")
                }
                .tag(2)
            
            TasksView()
                .tabItem {
                    Label("Tasks", systemImage: "checklist")
                }
                .tag(3)
        }
        .frame(minWidth: 900, minHeight: 700)
        .environmentObject(chatViewModel)
    }
}

#Preview {
    ContentView()
}
