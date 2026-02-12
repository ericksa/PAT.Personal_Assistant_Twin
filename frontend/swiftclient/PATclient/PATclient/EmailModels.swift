import Foundation

enum EmailCategory: String, Codable, CaseIterable {
    case work
    case personal
    case urgent
    case newsletter
    case spam
    case notification
    case marketing
    case social
    case financial
    case travel
}

struct PATEmail: Identifiable, Codable {
    let id: UUID?
    var subject: String
    var senderEmail: String
    var senderName: String?
    var bodyText: String?
    var receivedAt: String // ISO timestamp
    var read: Bool
    var flagged: Bool
    var category: EmailCategory?
    var priority: Int
    var summary: String?
    var folder: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case subject
        case senderEmail = "sender_email"
        case senderName = "sender_name"
        case bodyText = "body_text"
        case receivedAt = "received_at"
        case read
        case flagged
        case category
        case priority
        case summary
        case folder
    }
}

struct EmailResponse: Codable {
    let status: String
    let emails: [PATEmail]?
    let count: Int?
    let message: String?
}

struct EmailAnalytics: Codable {
    let totalEmails: Int
    let unreadCount: Int
    let flaggedCount: Int
    let urgentCount: Int
    let categories: [String: Int]
    
    enum CodingKeys: String, CodingKey {
        case totalEmails = "total_emails"
        case unreadCount = "unread_count"
        case flaggedCount = "flagged_count"
        case urgentCount = "urgent_count"
        case categories
    }
}

struct EmailAnalyticsResponse: Codable {
    let status: String
    let analytics: EmailAnalytics?
}
