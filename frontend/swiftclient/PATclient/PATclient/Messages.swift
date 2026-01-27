//
//  Message.swift
//  PATclient
//
//  Message model for chat interface
//

import Foundation

enum MessageType: Hashable {
    case user
    case assistant
    case system
}

struct Message: Identifiable, Codable, Hashable {
    let id: UUID
    let type: MessageType
    let content: String
    let timestamp: Date
    var sources: [Source] = []
    var toolsUsed: [String] = []
    var modelUsed: String = ""
    var processingTime: Double = 0.0
    
    init(id: UUID = UUID(), type: MessageType, content: String, timestamp: Date = Date(), sources: [Source] = [], toolsUsed: [String] = [], modelUsed: String = "", processingTime: Double = 0.0) {
        self.id = id
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.sources = sources
        self.toolsUsed = toolsUsed
        self.modelUsed = modelUsed
        self.processingTime = processingTime
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
        hasher.combine(type)
        hasher.combine(content)
        hasher.combine(timestamp)
        hasher.combine(sources)
        hasher.combine(toolsUsed)
        hasher.combine(modelUsed)
        hasher.combine(processingTime)
    }
    
    static func == (lhs: Message, rhs: Message) -> Bool {
        lhs.id == rhs.id &&
        lhs.type == rhs.type &&
        lhs.content == rhs.content &&
        lhs.timestamp == rhs.timestamp &&
        lhs.sources == rhs.sources &&
        lhs.toolsUsed == rhs.toolsUsed &&
        lhs.modelUsed == rhs.modelUsed &&
        lhs.processingTime == rhs.processingTime
    }
    
    enum CodingKeys: String, CodingKey {
        case id
        case type
        case content
        case timestamp
        case sources
        case toolsUsed = "tools_used"
        case modelUsed = "model_used"
        case processingTime = "processing_time"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(UUID.self, forKey: .id)
        let typeString = try container.decode(String.self, forKey: .type)
        switch typeString {
        case "user": type = .user
        case "assistant": type = .assistant
        case "system": type = .system
        default: type = .assistant
        }
        content = try container.decode(String.self, forKey: .content)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        sources = try container.decodeIfPresent([Source].self, forKey: .sources) ?? []
        toolsUsed = try container.decodeIfPresent([String].self, forKey: .toolsUsed) ?? []
        modelUsed = try container.decodeIfPresent(String.self, forKey: .modelUsed) ?? ""
        processingTime = try container.decodeIfPresent(Double.self, forKey: .processingTime) ?? 0.0
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        let typeString: String
        switch type {
        case .user: typeString = "user"
        case .assistant: typeString = "assistant"
        case .system: typeString = "system"
        }
        try container.encode(typeString, forKey: .type)
        try container.encode(content, forKey: .content)
        try container.encode(timestamp, forKey: .timestamp)
        try container.encode(sources, forKey: .sources)
        try container.encode(toolsUsed, forKey: .toolsUsed)
        try container.encode(modelUsed, forKey: .modelUsed)
        try container.encode(processingTime, forKey: .processingTime)
    }
}
