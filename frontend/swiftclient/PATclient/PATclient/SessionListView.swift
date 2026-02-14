//
//  SessionListView.swift
//  PATclient
//
//  Sidebar view for managing chat sessions with native macOS styling
//

import SwiftUI

struct SessionListView: View {
    @Binding var sessions: [ChatSession]
    @Binding var selectedSession: ChatSession
    var onCreateNew: () -> Void
    var onSelectSession: (ChatSession) -> Void
    var onDeleteSession: (ChatSession) -> Void

    @State private var sessionToDelete: ChatSession? = nil
    @State private var searchText: String = ""

    var filteredSessions: [ChatSession] {
        if searchText.isEmpty {
            return sortedSessions
        }
        return sortedSessions.filter { session in
            session.title.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.caption)
                    .foregroundColor(.secondary)

                TextField("Search chats...", text: $searchText)
                    .textFieldStyle(.plain)
                    .font(.subheadline)

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.borderless)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.secondary.opacity(0.05))
            .cornerRadius(8)
            .padding(.horizontal, 12)
            .padding(.top, 12)

            // Header
            headerView
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

            Divider()
                .padding(.horizontal, 12)

            // Session list
            if filteredSessions.isEmpty {
                emptyState
            } else {
                sessionList
            }

            Spacer()

            // Bottom stats
            HStack(spacing: 4) {
                Image(systemName: "tray.fill")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Text("\(sessions.count) sessions")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color.secondary.opacity(0.03))
        }
        .background(.ultraThinMaterial)
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
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.primary)

            Spacer()

            Button(action: onCreateNew) {
                Image(systemName: "plus")
                    .font(.system(size: 12, weight: .semibold))
            }
            .buttonStyle(.borderless)
            .help("New chat")
            .keyboardShortcut("n", modifiers: .command)
        }
    }

    @ViewBuilder
    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()

            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 40))
                .foregroundColor(.secondary.opacity(0.5))

            VStack(spacing: 4) {
                Text(searchText.isEmpty ? "No saved chats" : "No matching chats")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                if !searchText.isEmpty {
                    Text("Try a different search")
                        .font(.caption)
                        .foregroundColor(.secondary.opacity(0.7))
                }
            }

            if searchText.isEmpty {
                Button("Start a new chat", action: onCreateNew)
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                    .padding(.top, 8)
            }

            Spacer()
        }
        .frame(maxWidth: .infinity)
    }

    @ViewBuilder
    private var sessionList: some View {
        List(selection: $selectedSession) {
            Section {
                ForEach(filteredSessions) { session in
                    SessionRowView(
                        session: session,
                        isSelected: selectedSession.id == session.id,
                        onTap: { onSelectSession(session) },
                        onDelete: { sessionToDelete = session }
                    )
                    .tag(session)
                }
            } header: {
                if !searchText.isEmpty {
                    Text("Results")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .listStyle(.sidebar)
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
        HStack(spacing: 10) {
            // Icon
            ZStack {
                RoundedRectangle(cornerRadius: 6)
                    .fill(isSelected ? Color.accentColor.opacity(0.2) : Color.secondary.opacity(0.1))
                    .frame(width: 28, height: 28)

                Image(systemName: iconForSession)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(isSelected ? .accentColor : .secondary)
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(session.title)
                    .font(.subheadline)
                    .fontWeight(isSelected ? .semibold : .regular)
                    .lineLimit(1)
                    .foregroundColor(isSelected ? .primary : .primary)

                HStack(spacing: 4) {
                    Text("\(session.messages.count) messages")
                        .font(.caption2)
                    Text("•")
                        .font(.caption2)
                        .foregroundColor(.secondary.opacity(0.5))
                    Text(formattedDate(session.updatedAt))
                        .font(.caption2)
                }
                .foregroundColor(.secondary)
            }

            Spacer()

            if isHovered || isSelected {
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
        .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
        .cornerRadius(6)
        .contentShape(Rectangle())
        .onHover { hovering in
            isHovered = hovering
        }
        .onTapGesture {
            onTap()
        }
    }

    private var iconForSession: String {
        if session.title.lowercased().contains("email") {
            return "envelope"
        } else if session.title.lowercased().contains("calendar") || session.title.lowercased().contains("event") {
            return "calendar"
        } else if session.title.lowercased().contains("task") || session.title.lowercased().contains("todo") {
            return "checklist"
        } else if session.title.lowercased().contains("doc") || session.title.lowercased().contains("file") {
            return "doc.text"
        }
        return "bubble.left"
    }

    private func formattedDate(_ date: Date) -> String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
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
    .frame(width: 250, height: 500)
}
