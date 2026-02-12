import SwiftUI

struct EmailsView: View {
    @StateObject var viewModel = EmailsViewModel()
    @State private var selectedFolder = "INBOX"
    @State private var showingCompose = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if let analytics = viewModel.analytics {
                    AnalyticsHeader(analytics: analytics)
                }
                
                List {
                    if viewModel.isLoading && viewModel.emails.isEmpty {
                        ProgressView("Syncing emails...")
                    } else if viewModel.emails.isEmpty {
                        VStack(spacing: 20) {
                            Text("No emails found")
                                .foregroundColor(.secondary)
                            Button("Sync Now") {
                                Task { await viewModel.syncEmails() }
                            }
                            .buttonStyle(.bordered)
                        }
                        .frame(maxWidth: .infinity, minHeight: 200)
                    } else {
                        ForEach(viewModel.emails) { email in
                            EmailRow(email: email)
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
                                }
                        }
                    }
                }
            }
            .navigationTitle("Emails")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingCompose = true }) {
                        Image(systemName: "square.and.pencil")
                    }
                }
                ToolbarItem(placement: .navigation) {
                    Button(action: { 
                        Task { await viewModel.syncEmails() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .sheet(isPresented: $showingCompose) {
                EmailComposeView(viewModel: viewModel)
            }
            .onAppear {
                Task { await viewModel.fetchEmails() }
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
    }
}

struct EmailRow: View {
    let email: PATEmail
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(email.senderName ?? email.senderEmail)
                    .font(.headline)
                    .foregroundColor(email.read ? .primary : .blue)
                Spacer()
                Text(formatDate(email.receivedAt))
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
                    .padding(.top, 2)
            }
            
            HStack {
                if let category = email.category {
                    CategoryBadge(category: category)
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
            }
            .padding(.top, 2)
        }
        .padding(.vertical, 4)
    }
    
    private func formatDate(_ dateStr: String) -> String {
        // Simple relative date formatting
        return dateStr // For now
    }
}

struct CategoryBadge: View {
    let category: EmailCategory
    
    var color: Color {
        switch category {
        case .urgent: return .red
        case .work: return .blue
        case .personal: return .green
        case .financial: return .orange
        case .travel: return .purple
        default: return .gray
        }
    }
    
    var body: some View {
        Text(category.rawValue.uppercased())
            .font(.system(size: 8, weight: .bold))
            .padding(.horizontal, 4)
            .padding(.vertical, 1)
            .background(color.opacity(0.1))
            .foregroundColor(color)
            .cornerRadius(3)
    }
}

struct AnalyticsHeader: View {
    let analytics: EmailAnalytics
    
    var body: some View {
        HStack(spacing: 20) {
            StatView(label: "Unread", value: "\(analytics.unreadCount)", color: .blue)
            StatView(label: "Urgent", value: "\(analytics.urgentCount)", color: .red)
            StatView(label: "Flagged", value: "\(analytics.flaggedCount)", color: .orange)
            Spacer()
        }
        .padding()
        .background(Color.secondary.opacity(0.05))
    }
}

struct StatView: View {
    let label: String
    let value: String
    let color: Color
    
    var body: some View {
        VStack(alignment: .leading) {
            Text(value)
                .font(.headline)
                .foregroundColor(color)
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}
