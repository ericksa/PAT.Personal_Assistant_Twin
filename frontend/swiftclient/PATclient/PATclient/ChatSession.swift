//
//  ChatSession.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
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
     
     // Custom CodingKeys for ChatSession
     enum CodingKeys: String, CodingKey {
         case id, title, messages, createdAt, updatedAt, settings
     }
     
     // Custom decoding for backward compatibility
     init(from decoder: Decoder) throws {
         let container = try decoder.container(keyedBy: CodingKeys.self)
         id = try container.decode(UUID.self, forKey: .id)
         title = try container.decode(String.self, forKey: .title)
         messages = try container.decode([Message].self, forKey: .messages)
         createdAt = try container.decode(Date.self, forKey: .createdAt)
         updatedAt = try container.decode(Date.self, forKey: .updatedAt)
         settings = try container.decode(ChatSettings.self, forKey: .settings)
     }
     
     // Custom encoding
     func encode(to encoder: Encoder) throws {
         var container = encoder.container(keyedBy: CodingKeys.self)
         try container.encode(id, forKey: .id)
         try container.encode(title, forKey: .title)
         try container.encode(messages, forKey: .messages)
         try container.encode(createdAt, forKey: .createdAt)
         try container.encode(updatedAt, forKey: .updatedAt)
         try container.encode(settings, forKey: .settings)
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
    var llmProvider: String
    var selectedModel: String
    var temperature: Double
    var maxTokens: Int
    var useDarkMode: Bool
    
    init(useWebSearch: Bool = false, useMemoryContext: Bool = true, provider: String = "ollama", llmProvider: String = "ollama", selectedModel: String = "llama3", temperature: Double = 0.7, maxTokens: Int = 2048, useDarkMode: Bool = false) {
        self.useWebSearch = useWebSearch
        self.useMemoryContext = useMemoryContext
        self.provider = provider
        self.llmProvider = llmProvider
        self.selectedModel = selectedModel
        self.temperature = temperature
        self.maxTokens = maxTokens
        self.useDarkMode = useDarkMode
    }
    
    // Custom CodingKeys for backward compatibility
    enum CodingKeys: String, CodingKey {
        case useWebSearch, useMemoryContext, provider, llmProvider, selectedModel, temperature, maxTokens, useDarkMode
    }
    
    // Custom decoding to handle missing properties
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        
        // Required properties with defaults
        useWebSearch = try container.decodeIfPresent(Bool.self, forKey: .useWebSearch) ?? false
        useMemoryContext = try container.decodeIfPresent(Bool.self, forKey: .useMemoryContext) ?? true
        provider = try container.decodeIfPresent(String.self, forKey: .provider) ?? "ollama"
        temperature = try container.decodeIfPresent(Double.self, forKey: .temperature) ?? 0.7
        maxTokens = try container.decodeIfPresent(Int.self, forKey: .maxTokens) ?? 2048
        useDarkMode = try container.decodeIfPresent(Bool.self, forKey: .useDarkMode) ?? false
        
        // New properties with backward compatibility
        // If llmProvider is missing, fallback to provider
        llmProvider = try container.decodeIfPresent(String.self, forKey: .llmProvider) ?? provider
        
        // If selectedModel is missing, use default
        selectedModel = try container.decodeIfPresent(String.self, forKey: .selectedModel) ?? "llama3"
    }
    
    // Custom encoding
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(useWebSearch, forKey: .useWebSearch)
        try container.encode(useMemoryContext, forKey: .useMemoryContext)
        try container.encode(provider, forKey: .provider)
        try container.encode(llmProvider, forKey: .llmProvider)
        try container.encode(selectedModel, forKey: .selectedModel)
        try container.encode(temperature, forKey: .temperature)
        try container.encode(maxTokens, forKey: .maxTokens)
        try container.encode(useDarkMode, forKey: .useDarkMode)
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(useWebSearch)
        hasher.combine(useMemoryContext)
        hasher.combine(provider)
        hasher.combine(llmProvider)
        hasher.combine(selectedModel)
        hasher.combine(temperature)
        hasher.combine(maxTokens)
        hasher.combine(useDarkMode)
    }
    
    static func == (lhs: ChatSettings, rhs: ChatSettings) -> Bool {
        lhs.useWebSearch == rhs.useWebSearch &&
        lhs.useMemoryContext == rhs.useMemoryContext &&
        lhs.provider == rhs.provider &&
        lhs.llmProvider == rhs.llmProvider &&
        lhs.selectedModel == rhs.selectedModel &&
        lhs.temperature == rhs.temperature &&
        lhs.maxTokens == rhs.maxTokens &&
        lhs.useDarkMode == rhs.useDarkMode
    }
}
