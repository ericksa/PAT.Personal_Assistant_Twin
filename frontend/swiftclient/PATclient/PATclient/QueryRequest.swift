//
//  QueryRequest.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//


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
    
    init(query: String, user_id: String = "default", stream: Bool = false, tools: [String] = []) {
        self.query = query
        self.user_id = user_id
        self.stream = stream
        self.tools = tools
    }
}
