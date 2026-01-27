//
//  AgentService.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//


//
//  AgentService.swift
//  PATclient
//
//  Service for communicating with the agent backend
//

import Foundation

class AgentService {
    static let shared = AgentService()
    
    private let baseURL: String
    private let session: URLSession
    
    private init(baseURL: String = "http://127.0.0.1:8002") {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }
    func checkAgentService() async -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else { return false }
        do {
            let (_, response) = try await session.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse else { return false }
            return httpResponse.statusCode == 200
        } catch {
            print("Agent service not reachable: \(error)")
            return false
        }
    }
    func query(text: String, webSearch: Bool, useMemory: Bool = true, userId: String = "default", stream: Bool = false) async throws -> QueryResponse {
        var tools: [String] = []
        if webSearch {
            tools.append("web")
        }
        if useMemory {
            tools.append("memory")
        }
        
        let request = QueryRequest(query: text, user_id: userId, stream: stream, tools: tools)
        
        guard let url = URL(string: "\(baseURL)/query") else {
            throw AgentError.invalidURL
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await session.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AgentError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw AgentError.serverError(httpResponse.statusCode)
        }
        
        let queryResponse = try JSONDecoder().decode(QueryResponse.self, from: data)
        return queryResponse
    }
    
    func checkHealth() async throws -> HealthStatus {
        guard let url = URL(string: "\(baseURL)/health") else {
            throw AgentError.invalidURL
        }
        
        let (data, response) = try await session.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw AgentError.invalidResponse
        }
        
        return try JSONDecoder().decode(HealthStatus.self, from: data)
    }
}

struct QueryResponse: Codable {
    let response: String
    let sources: [Source]
    let tools_used: [String]
    let model_used: String
    let processing_time: Double
}

enum AgentError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingError:
            return "Failed to decode response"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}

struct HealthStatus: Codable {
    let status: String
    let services: ServiceStatus
    
    struct ServiceStatus: Codable {
        let database: String
        let redis: String
        let ingest: String
        let llm_provider: String
    }
}
