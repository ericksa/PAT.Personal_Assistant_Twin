import SwiftUI

struct EmailsView: View {
    @StateObject var viewModel = EmailsViewModel()
    @State private var selectedFolder = "INBOX"
    @State private var showingCompose = false
    @State private var selectedEmail: PATEmail?
    @State private var searchText: String = ""

    let folders = ["INBOX", "Sent", "Drafts", "Archive"]

    var filteredEmails: [PATEmail] {
        if searchText.isEmpty {
            return viewModel.emails
        }
        return viewModel.emails.filter { email in
            email.subject.localizedCaseInsensitiveContains(searchText) ||
            (email.senderName ?? "").localizedCaseInsensitiveContains(searchText) ||
            (email.senderEmail).localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationSplitView {
            // Sidebar with folders
            VStack(spacing: 0) {
                Text("Mail")
                    .font(.headline)
                    .fontWeight(.semibold)
                    .padding()

                Divider()

                // Search bar
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    TextField("Search emails...", text: $searchText)
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
                .padding(.top, 8)

                // Folders
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(folders.enumerated()), id: \.element) { index, folder in
                        FolderRow(
                            folder: folder,
                            isSelected: selectedFolder == folder,
                            unreadCount: unreadCount(for: folder)
                        ) {
                            selectedFolder = folder
                            Task { await viewModel.fetchEmails(folder: folder) }
                        }
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Divider()

                // Quick actions
                VStack(alignment: .leading, spacing: 8) {
                    Button(action: { Task { await viewModel.syncEmails() } }) {
                        Label("Sync Now", systemImage: "arrow.clockwise")
                            .font(.subheadline)
                    }
                    .buttonStyle(.borderless)

                    Button(action: { showingCompose = true }) {
                        Label("Compose", systemImage: "square.and.pencil")
                            .font(.subheadline)
                    }
                    .buttonStyle(.bordered)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Spacer()

                // Analytics summary
                if let analytics = viewModel.analytics {
                    EmailAnalyticsSummary(analytics: analytics)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                }
            }
            .nativeSidebar()
            .navigationSplitViewColumnWidth(min: 200, ideal: 240)
        } content: {
            // Email list
            VStack(spacing: 0) {
                HStack {
                    Text(selectedFolder.capitalized)
                        .font(.headline)

                    Spacer()

                    Text("\(filteredEmails.count) emails")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(.ultraThinMaterial)

                Divider()

                List(selection: $selectedEmail) {
                    if viewModel.isLoading && viewModel.emails.isEmpty {
                        ProgressView("Loading...")
                            .frame(maxWidth: .infinity, alignment: .center)
                    } else if filteredEmails.isEmpty {
                        EmptyStateView(
                            icon: "envelope.open",
                            title: "No Emails",
                            message: "Your inbox is empty"
                        )
                    } else {
                        ForEach(filteredEmails) { email in
                            ModernEmailRow(
                                email: email,
                                isSelected: selectedEmail?.id == email.id
                            )
                            .tag(email)
                            .contextMenu {
                                Button {
                                    Task { await viewModel.classifyEmail(email) }
                                } label: {
                                    Label("AI Classify", systemImage: "sparkles")
                                }

                                Button {
                                    Task { await viewModel.archiveEmail(email) }
                                } label: {
                                    Label("Archive", systemImage: "archivebox")
                                }

                                Divider()

                                Button {
                                    Task { await viewModel.deleteEmail(email) }
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                                .foregroundColor(.red)
                            }
                        }
                    }
                }
                .listStyle(.plain)
            }
            .background(Color(nsColor: .windowBackgroundColor))
        } detail: {
            // Email detail
            if let email = selectedEmail {
                EmailDetailView(email: email, viewModel: viewModel)
            } else {
                EmptyStateView(
                    icon: "envelope",
                    title: "Select an Email",
                    message: "Choose an email to view its contents"
                )
            }
        }
        .sheet(isPresented: $showingCompose) {
            EmailComposeView(viewModel: viewModel)
                .frame(minWidth: 600, minHeight: 500)
        }
        .task {
            await viewModel.fetchEmails(folder: selectedFolder)
        }
        .alert("Error", isPresented: Binding<Bool>(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    private func unreadCount(for folder: String) -> Int {
        // In production, this should query actual counts
        return 0
    }
}

// MARK: - Folder Row
struct FolderRow: View {
    let folder: String
    let isSelected: Bool
    let unreadCount: Int
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: folderIcon)
                    .font(.system(size: 14))
                    .foregroundColor(isSelected ? .accentColor : .secondary)
                    .frame(width: 20)

                Text(folder.capitalized)
                    .font(.subheadline)
                    .foregroundColor(isSelected ? .primary : .primary)

                Spacer()

                if unreadCount > 0 {
                    Text("\(unreadCount)")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.accentColor)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }

                if isSelected {
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.accentColor)
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }

    private var folderIcon: String {
        switch folder.uppercased() {
        case "INBOX": return "tray"
        case "SENT": return "paperplane"
        case "DRAFTS": return "doc.plaintext"
        case "ARCHIVE": return "archivebox"
        case "TRASH": return "trash"
        default: return "folder"
        }
    }
}

// MARK: - Modern Email Row
struct ModernEmailRow: View {
    let email: PATEmail
    let isSelected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                HStack(spacing: 4) {
                    if !email.read {
                        Circle()
                            .fill(Color.accentColor)
                            .frame(width: 8, height: 8)
                    }

                    Text(email.senderName ?? email.senderEmail)
                        .font(.subheadline)
                        .fontWeight(email.read ? .regular : .semibold)
                        .foregroundColor(email.read ? .primary : .primary)
                }

                Spacer()

                Text(formattedDate(email.receivedAt))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Text(email.subject)
                .font(.subheadline)
                .lineLimit(1)

            if let summary = email.summary {
                Text(summary)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            HStack(spacing: 8) {
                if let category = email.category {
                    EmailCategoryBadge(category: category)
                }

                if email.priority >= 7 {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundColor(.red)
                        .font(.caption)
                }

                if email.flagged {
                    Image(systemName: "flag.fill")
                        .foregroundColor(.orange)
                        .font(.caption)
                }

                Spacer()

                if email.hasAttachments {
                    Image(systemName: "paperclip")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
        .background(isSelected ? Color.accentColor.opacity(0.05) : Color.clear)
        .contentShape(Rectangle())
    }

    private func formattedDate(_ dateStr: String) -> String {
        // Simple date formatting - in production, use proper date parsing
        return dateStr
    }
}

// MARK: - Email Category Badge
struct EmailCategoryBadge: View {
    let category: EmailCategory

    var body: some View {
        Text(category.rawValue.uppercased())
            .font(.caption2)
            .fontWeight(.semibold)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(categoryColor.opacity(0.1))
            .foregroundColor(categoryColor)
            .cornerRadius(4)
    }

    private var categoryColor: Color {
        switch category {
        case .urgent: return .red
        case .work: return .blue
        case .personal: return .green
        case .financial: return .orange
        case .travel: return .purple
        default: return .gray
        }
    }
}

// MARK: - Email Analytics Summary
struct EmailAnalyticsSummary: View {
    let analytics: EmailAnalytics

    var body: some View {
        VStack(spacing: 12) {
            Divider()

            HStack {
                Text("Inbox Overview")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.secondary)
                Spacer()
            }

            HStack(spacing: 16) {
                EmailStat(value: analytics.unreadCount, label: "Unread", color: .blue)
                EmailStat(value: analytics.urgentCount, label: "Urgent", color: .red)
                EmailStat(value: analytics.flaggedCount, label: "Flagged", color: .orange)
            }
        }
    }
}

struct EmailStat: View {
    let value: Int
    let label: String
    let color: Color

    var body: some View {
        VStack(spacing: 2) {
            Text("\(value)")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(color)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Email Detail View
struct EmailDetailView: View {
    let email: PATEmail
    let viewModel: EmailsViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(email.subject)
                            .font(.title3)
                            .fontWeight(.bold)

                        Spacer()

                        if email.flagged {
                            Image(systemName: "flag.fill")
                                .foregroundColor(.orange)
                        }
                    }

                    HStack(spacing: 12) {
                        if let category = email.category {
                            EmailCategoryBadge(category: category)
                        }

                        if email.priority >= 7 {
                            HStack(spacing: 4) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.red)
                                Text("High Priority")
                                    .font(.caption)
                                    .foregroundColor(.red)
                            }
                        }
                    }
                }

                Divider()

                // Sender info
                HStack(spacing: 12) {
                    ZStack {
                        Circle()
                            .fill(Color.accentColor.opacity(0.2))
                            .frame(width: 44, height: 44)
                        Text(String((email.senderName ?? email.senderEmail).prefix(1).uppercased()))
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundColor(.accentColor)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Text(email.senderName ?? email.senderEmail)
                            .font(.headline)
                        Text(email.senderEmail)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    VStack(alignment: .trailing, spacing: 2) {
                        Text(email.receivedAt)
                            .font(.subheadline)
                        if let time = extractTime(from: email.receivedAt) {
                            Text(time)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }

                Divider()

                // Body
                if let body = email.body {
                    Text(body)
                        .font(.body)
                        .lineSpacing(4)
                } else {
                    Text("No message body")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .italic()
                }

                Spacer()
            }
            .padding(20)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button(action: {
                    Task { await viewModel.classifyEmail(email) }
                }) {
                    Image(systemName: "sparkles")
                }
                .help("AI Classify")

                Button(action: {
                    Task { await viewModel.archiveEmail(email) }
                }) {
                    Image(systemName: "archivebox")
                }
                .help("Archive")

                Button(action: {
                    // Reply functionality
                }) {
                    Image(systemName: "arrowshape.turn.up.left")
                }
                .help("Reply")
            }
        }
    }

    private func extractTime(from dateStr: String) -> String? {
        // Simple time extraction - in production, use proper date parsing
        return nil
    }
}

#Preview {
    EmailsView()
}
