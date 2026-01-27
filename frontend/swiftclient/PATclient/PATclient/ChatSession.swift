//
//  ChatSession.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//


//
//  ChatSession.swift
//  PATclient
//
//  Chat session model for persistence
//

import Foundation

struct ChatSession: Identifiable, Codable, Hashable {
    let id: UUID
    var title: String
    var messages: [Message]
    let createdAt: Date
    var updatedAt: Date
    var settings: ChatSettings
    
    init(id: UUID = UUID(), title: String, messages: [Message] = [], createdAt: Date = Date(), updatedAt: Date = Date(), settings: ChatSettings = ChatSettings()) {
        self.id = id
        self.title = title
        self.messages = messages
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.settings = settings
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
        hasher.combine(title)
        hasher.combine(messages)
        hasher.combine(createdAt)
        hasher.combine(updatedAt)
        hasher.combine(settings)
    }
    
    static func == (lhs: ChatSession, rhs: ChatSession) -> Bool {
        lhs.id == rhs.id &&
        lhs.title == rhs.title &&
        lhs.messages == rhs.messages &&
        lhs.createdAt == rhs.createdAt &&
        lhs.updatedAt == rhs.updatedAt &&
        lhs.settings == rhs.settings
    }
}

struct ChatSettings: Codable, Hashable {
    var useWebSearch: Bool
    var useMemoryContext: Bool
    var provider: String
    var temperature: Double
    var maxTokens: Int
    
    init(useWebSearch: Bool = false, useMemoryContext: Bool = true, provider: String = "ollama", temperature: Double = 0.7, maxTokens: Int = 2048) {
        self.useWebSearch = useWebSearch
        self.useMemoryContext = useMemoryContext
        self.provider = provider
        self.temperature = temperature
        self.maxTokens = maxTokens
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(useWebSearch)
        hasher.combine(useMemoryContext)
        hasher.combine(provider)
        hasher.combine(temperature)
        hasher.combine(maxTokens)
    }
    
    static func == (lhs: ChatSettings, rhs: ChatSettings) -> Bool {
        lhs.useWebSearch == rhs.useWebSearch &&
        lhs.useMemoryContext == rhs.useMemoryContext &&
        lhs.provider == rhs.provider &&
        lhs.temperature == rhs.temperature &&
        lhs.maxTokens == rhs.maxTokens
    }
}
