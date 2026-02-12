import Foundation

struct Message: Identifiable, Codable, Hashable {
    enum MessageType: String, Codable {
        case user, assistant, system
    }
    
    let id: UUID
    let type: MessageType
    let content: String
    let timestamp: Date
    var sources: [Source]
    var toolsUsed: [String]
    var modelUsed: String
    var processingTime: Double

    init(
        id: UUID = UUID(),
        type: MessageType,
        content: String,
        timestamp: Date = Date(),
        sources: [Source] = [],
        toolsUsed: [String] = [],
        modelUsed: String = "",
        processingTime: Double = 0
    ) {
        self.id = id
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.sources = sources
        self.toolsUsed = toolsUsed
        self.modelUsed = modelUsed
        self.processingTime = processingTime
    }
}
