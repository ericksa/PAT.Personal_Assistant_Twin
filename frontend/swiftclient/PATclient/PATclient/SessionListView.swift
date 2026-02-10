//
//  SessionListView.swift
//  PATclient
//
//  Sidebar view for managing chat sessions
//

import SwiftUI

struct SessionListView: View {
    @Binding var sessions: [ChatSession]
    @Binding var selectedSession: ChatSession
    var onCreateNew: () -> Void
    var onSelectSession: (ChatSession) -> Void
    var onDeleteSession: (ChatSession) -> Void
    
    // Move dialog state to parent to avoid focus issues
    @State private var sessionToDelete: ChatSession? = nil
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView
            
            Divider()
            
            // Session list
            if sessions.isEmpty {
                emptyState
            } else {
                sessionList
            }
        }
        .background(Color(nsColor: .controlBackgroundColor))
        // Alert bound to parent view to prevent focus loss
        .alert(
            "Delete Chat?",
            isPresented: Binding(
                get: { sessionToDelete != nil },
                set: { if !$0 { sessionToDelete = nil } }
            ),
            presenting: sessionToDelete
        ) { session in
            Button("Cancel", role: .cancel) {
                sessionToDelete = nil
            }
            Button("Delete", role: .destructive) {
                onDeleteSession(session)
                sessionToDelete = nil
            }
        } message: { session in
            Text("Are you sure you want to delete \"\(session.title)\"? This cannot be undone.")
        }
    }
    
    @ViewBuilder
    private var headerView: some View {
        HStack {
            Text("Chats")
                .font(.headline)
            
            Spacer()
            
            Button(action: onCreateNew) {
                Image(systemName: "plus")
                    .font(.system(size: 14, weight: .medium))
            }
            .buttonStyle(.borderless)
            .help("New chat")
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
    }
    
    @ViewBuilder
    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "tray")
                .font(.system(size: 40))
                .foregroundColor(.secondary)
            
            Text("No saved chats")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    @ViewBuilder
    private var sessionList: some View {
        List(selection: $selectedSession) {
            ForEach(sortedSessions) { session in
                SessionRowView(
                    session: session,
                    isSelected: selectedSession.id == session.id,
                    onTap: { onSelectSession(session) },
                    onDelete: { sessionToDelete = session }  // Set here, present in parent
                )
                .tag(session)
            }
        }
        .listStyle(.plain)
    }
    
    private var sortedSessions: [ChatSession] {
        sessions.sorted { $0.updatedAt > $1.updatedAt }
    }
}

struct SessionRowView: View {
    let session: ChatSession
    let isSelected: Bool
    let onTap: () -> Void
    let onDelete: () -> Void
    
    @State private var isHovered = false
    
    var body: some View {
        HStack(spacing: 8) {
            VStack(alignment: .leading, spacing: 2) {
                Text(session.title)
                    .font(.subheadline)
                    .fontWeight(isSelected ? .semibold : .regular)
                    .lineLimit(1)
                
                Text("\(session.messages.count) messages • \(session.updatedAt, style: .relative)")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            if isHovered {
                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.borderless)
                .help("Delete chat")
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
        .background(isSelected ? Color.accentColor.opacity(0.15) : Color.clear)
        .cornerRadius(6)
        .contentShape(Rectangle())
        .onHover { hovering in
            isHovered = hovering
        }
        .onTapGesture {
            onTap()
        }
    }
}

#Preview {
    SessionListView(
        sessions: .constant([
            ChatSession(title: "Weather inquiry", messages: [
                Message(type: .user, content: "What's the weather?"),
                Message(type: .assistant, content: "It's sunny!")
            ]),
            ChatSession(title: "Document search", messages: [
                Message(type: .user, content: "Find my resume")
            ])
        ]),
        selectedSession: .constant(ChatSession(title: "Test")),
        onCreateNew: {},
        onSelectSession: { _ in },
        onDeleteSession: { _ in }
    )
    .frame(width: 250, height: 400)
}
