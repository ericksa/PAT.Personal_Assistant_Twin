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
            email.senderEmail.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationSplitView {
            sidebar
                .navigationSplitViewColumnWidth(min: 200, ideal: 240)
        } content: {
            emailList
                .background(Color(nsColor: .windowBackgroundColor))
        } detail: {
            emailDetail
        }
        .sheet(isPresented: $showingCompose) {
            emailComposeView
        }
        .task {
            await viewModel.fetchEmails(folder: selectedFolder)
        }
        .alert("Error", isPresented: $viewModel.hasError) {
            Button("OK", role: .cancel) { }
        } message: {
            if let message = viewModel.errorMessage {
                Text(message)
            }
        }
    }
    
    private var sidebar: some View {
        VStack(spacing: 0) {
            Text("Mail")
                .font(.headline)
                .fontWeight(.semibold)
                .padding()
            
            Divider()
            
            searchBar
            
            folderList
            
            Divider()
            
            quickActions
            
            Spacer()
            
            if let analytics = viewModel.analytics {
                analyticsSummary(analytics: analytics)
            }
        }
        .background(.sideBarBackground)
        .nativeSidebar()
    }
    
    private var searchBar: some View {
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
    }
    
    private var folderList: some View {
        VStack(alignment: .leading, spacing: 2) {
            ForEach(folders, id: \.self) { folder in
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
    }
    
    private var quickActions: some View {
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
    }
    
    private func analyticsSummary(analytics: EmailAnalytics) -> some View {
        EmailAnalyticsSummary(analytics: analytics)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
    }
    
    private var emailList: some View {
        VStack(spacing: 0) {
            emailListHeader
            
            Divider()
            
            emailListContent
        }
    }
    
    private var emailListHeader: some View {
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
    }
    
    @ViewBuilder
    private var emailListContent: some View {
        if viewModel.isLoading && viewModel.emails.isEmpty {
            loadingView
        } else if filteredEmails.isEmpty {
            emptyView
        } else {
            emailListView
        }
    }
    
    private var loadingView: some View {
        ProgressView("Loading...")
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .center)
    }
    
    private var emptyView: some View {
        EmptyStateView(
            icon: "envelope.open",
            title: "No Emails",
            message: "Your inbox is empty"
        )
    }
    
    private var emailListView: some View {
        List(selection: $selectedEmail) {
            ForEach(filteredEmails) { email in
                ModernEmailRow(
                    email: email,
                    isSelected: selectedEmail?.id == email.id
                )
                .tag(email)
                .contextMenu {
                    emailContextMenu(email: email)
                }
            }
        }
        .listStyle(.plain)
    }
    
    private func emailContextMenu(email: PATEmail) -> some View {
        Group {
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
    
    private var emailDetail: some View {
        Group {
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
    }
    
    private var emailComposeView: some View {
        EmailComposeView(viewModel: viewModel)
            .frame(minWidth: 600, minHeight: 500)
    }

    private func unreadCount(for folder: String) -> Int {
        // In production, this should query actual counts
        return 0
    }
}

// MARK: - Helper Extensions

extension Color {
    static let sideBarBackground = Color(nsColor: .underPageBackgroundColor)
}
extension View {
    func nativeSidebar() -> some View {
#if os(macOS)
        self.background(Color(.windowBackgroundColor))
#else
        self
#endif
    }
}

// ... Keep the rest of your views (FolderRow, ModernEmailRow, EmailCategoryBadge, etc.) the same as before ...
//
// From this point, include all the remaining components exactly as in your original file:
// - FolderRow
// - ModernEmailRow
// - EmailCategoryBadge
// - EmailAnalyticsSummary
// - EmailStat
// - EmailDetailView

