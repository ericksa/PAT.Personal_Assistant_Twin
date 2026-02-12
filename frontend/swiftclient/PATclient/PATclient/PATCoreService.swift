import Foundation

class PATCoreService {
    static let shared = PATCoreService()
    
    private let baseURL: String
    private let session: URLSession
    
    private init(baseURL: String = Config.patCoreBaseURL) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)
    }
    
    // MARK: - Health
    
    func checkHealth() async -> Bool {
        guard let url = URL(string: "\(baseURL)/pat/health") else { return false }
        do {
            let (data, response) = try await session.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else { return false }
            
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
            return json?["status"] as? String == "healthy"
        } catch {
            return false
        }
    }
    
    // MARK: - Calendar
    
    func listEvents() async throws -> [CalendarEvent] {
        guard let url = URL(string: "\(baseURL)/pat/calendar/events?limit=50") else {
            throw PATCoreError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        
        let calendarResponse = try JSONDecoder().decode(CalendarResponse.self, from: data)
        return calendarResponse.events ?? []
    }
    
    func createEvent(_ event: CalendarEvent) async throws -> CalendarEvent {
        guard let url = URL(string: "\(baseURL)/pat/calendar/events") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(event)
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        // The API might return the created event or a success status
        // Based on reference, it returns the event in a standard response format or similar
        let calendarResponse = try JSONDecoder().decode(CalendarResponse.self, from: data)
        if let firstEvent = calendarResponse.events?.first {
            return firstEvent
        } else if let singleEvent = try? JSONDecoder().decode(CalendarEvent.self, from: data) {
            return singleEvent
        }
        throw PATCoreError.decodingError
    }
    
    func updateEvent(id: UUID, event: PartialCalendarEvent) async throws {
        guard let url = URL(string: "\(baseURL)/pat/calendar/events/\(id.uuidString)") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(event)
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    func deleteEvent(id: UUID) async throws {
        guard let url = URL(string: "\(baseURL)/pat/calendar/events/\(id.uuidString)") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    func rescheduleEvent(id: UUID) async throws -> RescheduleSuggestion {
        guard let url = URL(string: "\(baseURL)/pat/calendar/events/\(id.uuidString)/reschedule") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        return try JSONDecoder().decode(RescheduleSuggestion.self, from: data)
    }
    
    // MARK: - Tasks
    
    func listTasks(status: TaskStatus? = nil) async throws -> [PATTask] {
        var urlString = "\(baseURL)/pat/tasks?limit=50"
        if let status = status {
            urlString += "&status=\(status.rawValue)"
        }
        
        guard let url = URL(string: urlString) else {
            throw PATCoreError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        try validateResponse(response)
        
        let taskResponse = try JSONDecoder().decode(TaskResponse.self, from: data)
        return taskResponse.tasks ?? []
    }
    
    func createTask(_ task: PATTask) async throws -> PATTask {
        guard let url = URL(string: "\(baseURL)/pat/tasks") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(task)
        
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        
        let taskResponse = try JSONDecoder().decode(TaskResponse.self, from: data)
        if let firstTask = taskResponse.tasks?.first {
            return firstTask
        } else if let singleTask = try? JSONDecoder().decode(PATTask.self, from: data) {
            return singleTask
        }
        throw PATCoreError.decodingError
    }
    
    func completeTask(id: UUID, notes: String? = nil) async throws {
        guard let url = URL(string: "\(baseURL)/pat/tasks/\(id.uuidString)/complete") else {
            throw PATCoreError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let notes = notes {
            let body = ["notes": notes]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    func batchCreateTasks(descriptions: [String]) async throws {
        guard let url = URL(string: "\(baseURL)/pat/tasks/batch-create") else {
            throw PATCoreError.invalidURL
        }
        
        let requestBody = BatchTaskRequest(taskDescriptions: descriptions)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(requestBody)
        
        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }
    
    // MARK: - Helpers
    
    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw PATCoreError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            throw PATCoreError.serverError(httpResponse.statusCode)
        }
    }
}

enum PATCoreError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .invalidResponse: return "Invalid response from server"
        case .serverError(let code): return "Server error: \(code)"
        case .decodingError: return "Failed to decode response"
        }
    }
}

struct PartialCalendarEvent: Codable {
    var title: String?
    var description: String?
    var startDate: String?
    var startTime: String?
    var endDate: String?
    var endTime: String?
    var location: String?
    var eventType: String?
    var priority: Int?
    
    enum CodingKeys: String, CodingKey {
        case title, description, location, priority
        case startDate = "start_date"
        case startTime = "start_time"
        case endDate = "end_date"
        case endTime = "end_time"
        case eventType = "event_type"
    }
}
