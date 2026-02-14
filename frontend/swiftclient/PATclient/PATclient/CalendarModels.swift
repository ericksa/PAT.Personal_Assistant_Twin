import Foundation

struct CalendarEvent: Identifiable, Codable, Hashable {
    let id: UUID?
    var title: String
    var description: String?
    var startDate: String // YYYY-MM-DD
    var startTime: String? // HH:MM
    var endDate: String // YYYY-MM-DD
    var endTime: String? // HH:MM
    var location: String?
    var eventType: String
    var priority: Int?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case startDate = "start_date"
        case startTime = "start_time"
        case endDate = "end_date"
        case endTime = "end_time"
        case location
        case eventType = "event_type"
        case priority
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id ?? UUID())
        hasher.combine(title)
        hasher.combine(startDate)
    }

    static func == (lhs: CalendarEvent, rhs: CalendarEvent) -> Bool {
        lhs.id == rhs.id
    }
}

struct CalendarResponse: Codable {
    let status: String
    let events: [CalendarEvent]?
    let count: Int?
    let message: String?
}

struct RescheduleSuggestion: Codable {
    struct SuggestedTime: Codable {
        let date: String
        let time: String
        let reason: String
    }
    let suggestedTime: SuggestedTime
    let alternatives: [SuggestedTime]?
    
    enum CodingKeys: String, CodingKey {
        case suggestedTime = "suggested_time"
        case alternatives
    }
}
