//
//  Item.swift
//  PATApp
//
//  Created by PAT on 2/13/26.
//

import Foundation

/// Represents an item from the backend API
/// Matches the backend Pydantic model structure
struct Item: Codable, Identifiable, Equatable {
    let id: UUID
    let name: String
    let description: String?
    let category: String?
    let isActive: Bool
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case description
        case category
        case isActive = "is_active"
        case createdAt = "created_at"
    }
    
    /// Convenience initializer for testing and previews
    init(
        id: UUID = UUID(),
        name: String,
        description: String? = nil,
        category: String? = nil,
        isActive: Bool = true,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.isActive = isActive
        self.createdAt = createdAt
    }
}

// MARK: - API Response Models

/// Response model for paginated item lists
struct ItemsResponse: Codable {
    let items: [Item]
    let total: Int
    let skip: Int
    let limit: Int
}

/// Request model for creating a new item
struct CreateItemRequest: Codable {
    let name: String
    let description: String?
    let category: String?
    let isActive: Bool?
}

/// Request model for updating an existing item
struct UpdateItemRequest: Codable {
    let name: String?
    let description: String?
    let category: String?
    let isActive: Bool?
}
