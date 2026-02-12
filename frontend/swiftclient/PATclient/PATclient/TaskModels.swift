import Foundation

enum TaskPriority: String, Codable, CaseIterable, Hashable {
    case urgent
    case high
    case medium
    case low
}

enum TaskStatus: String, Codable, CaseIterable, Hashable {
    case pending
    case completed
    case cancelled
}

struct PATTask: Identifiable, Codable {
    let id: UUID?
    var title: String
    var description: String?
    var status: TaskStatus
    var priority: TaskPriority
    var dueDate: String? // ISO timestamp
    var tags: [String]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case status
        case priority
        case dueDate = "due_date"
        case tags
    }
}

struct TaskResponse: Codable {
    let status: String
    let tasks: [PATTask]?
    let count: Int?
    let message: String?
}

struct BatchTaskRequest: Codable {
    let taskDescriptions: [String]
    
    enum CodingKeys: String, CodingKey {
        case taskDescriptions = "task_descriptions"
    }
}
