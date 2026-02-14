//
//  QueryRequest.swift
//  PATclient
//
//  Request model for agent queries
//

import Foundation

struct QueryRequest: Codable {
    let query: String
    let user_id: String
    let stream: Bool
    let tools: [String]
    let llm_provider: String?
    let model: String?

    init(query: String, user_id: String = "default", stream: Bool = false, tools: [String] = [], llm_provider: String? = nil, model: String? = nil) {
        self.query = query
        self.user_id = user_id
        self.stream = stream
        self.tools = tools
        self.llm_provider = llm_provider
        self.model = model
    }

    enum CodingKeys: String, CodingKey {
        case query
        case user_id
        case stream
        case tools
        case llm_provider
        case model
    }
}
