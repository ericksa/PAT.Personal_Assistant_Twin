import Foundation
import Combine

@MainActor
class EmailsViewModel: ObservableObject {
    @Published var emails: [PATEmail] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var analytics: EmailAnalytics?
    
    private let service = PATCoreService.shared
    
    func fetchEmails(folder: String? = nil, isUnreadOnly: Bool = false) async {
        isLoading = true
        errorMessage = nil
        
        do {
            emails = try await service.listEmails(folder: folder, isUnreadOnly: isUnreadOnly)
            await fetchAnalytics()
        } catch {
            errorMessage = "Failed to load emails: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func fetchAnalytics() async {
        do {
            analytics = try await service.getEmailAnalytics()
        } catch {
            print("Failed to load analytics: \(error)")
        }
    }
    
    func syncEmails() async {
        isLoading = true
        do {
            _ = try await service.syncEmails()
            await fetchEmails()
        } catch {
            errorMessage = "Failed to sync emails: \(error.localizedDescription)"
        }
        isLoading = false
    }
    
    func archiveEmail(_ email: PATEmail) async {
        guard let id = email.id else { return }
        do {
            try await service.archiveEmail(id: id)
            emails.removeAll { $0.id == id }
            await fetchAnalytics()
        } catch {
            errorMessage = "Failed to archive email: \(error.localizedDescription)"
        }
    }
    
    func classifyEmail(_ email: PATEmail) async {
        guard let id = email.id else { return }
        do {
            try await service.classifyEmail(id: id)
            // Re-fetch this email to update its category
            await fetchEmails()
        } catch {
            errorMessage = "Failed to classify email: \(error.localizedDescription)"
        }
    }
}
