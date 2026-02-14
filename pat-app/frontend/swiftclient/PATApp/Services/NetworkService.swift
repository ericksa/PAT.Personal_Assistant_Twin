//
//  NetworkService.swift
//  PATApp
//
//  Created by PAT on 2/13/26.
//

import Foundation
import Combine

/// Errors that can occur during network operations
enum NetworkError: Error, Equatable {
    case invalidURL
    case invalidResponse
    case decodingError(String)
    case encodingError(String)
    case serverError(Int, String?)
    case networkFailure(Error)
    case unknown
    
    static func == (lhs: NetworkError, rhs: NetworkError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidURL, .invalidURL),
             (.invalidResponse, .invalidResponse),
             (.unknown, .unknown):
            return true
        case let (.decodingError(lhsMsg), .decodingError(rhsMsg)),
             let (.encodingError(lhsMsg), .encodingError(rhsMsg)):
            return lhsMsg == rhsMsg
        case let (.serverError(lhsCode, _), .serverError(rhsCode, _)):
            return lhsCode == rhsCode
        default:
            return false
        }
    }
    
    var localizedDescription: String {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError(let message):
            return "Failed to decode response: \(message)"
        case .encodingError(let message):
            return "Failed to encode request: \(message)"
        case .serverError(let code, let message):
            return "Server error \(code): \(message ?? "Unknown error")"
        case .networkFailure(let error):
            return "Network failure: \(error.localizedDescription)"
        case .unknown:
            return "Unknown error occurred"
        }
    }
}

/// Protocol defining network service operations
protocol NetworkServiceProtocol {
    func fetch<T: Decodable>(_ endpoint: String, queryItems: [URLQueryItem]?) async throws -> T
    func post<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T
    func put<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T
    func delete(_ endpoint: String) async throws
}

/// Service responsible for all network operations
/// Targets backend at http://localhost:8000/api/v1
actor NetworkService: NetworkServiceProtocol {
    
    // MARK: - Configuration
    
    /// Base URL for the backend API
    private let baseURL: String
    
    /// URLSession instance for network requests
    private let session: URLSession
    
    /// JSON decoder configured for API responses
    private let decoder: JSONDecoder
    
    /// JSON encoder configured for API requests
    private let encoder: JSONEncoder
    
    // MARK: - Initialization
    
    init(
        baseURL: String = "http://localhost:8000/api/v1",
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.session = session
        
        // Configure decoder for ISO8601 dates
        self.decoder = JSONDecoder()
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        dateFormatter.timeZone = TimeZone(secondsFromGMT: 0)
        decoder.dateDecodingStrategy = .formatted(dateFormatter)
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        
        // Configure encoder
        self.encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase
    }
    
    // MARK: - HTTP Methods
    
    /// Performs a GET request
    /// - Parameters:
    ///   - endpoint: The API endpoint (e.g., "/items")
    ///   - queryItems: Optional query parameters
    /// - Returns: Decoded response object
    func fetch<T: Decodable>(_ endpoint: String, queryItems: [URLQueryItem]? = nil) async throws -> T {
        guard let url = buildURL(endpoint: endpoint, queryItems: queryItems) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        return try await performRequest(request)
    }
    
    /// Performs a POST request
    /// - Parameters:
    ///   - endpoint: The API endpoint
    ///   - body: The request body to encode
    /// - Returns: Decoded response object
    func post<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        guard let url = buildURL(endpoint: endpoint) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        do {
            request.httpBody = try encoder.encode(body)
        } catch {
            throw NetworkError.encodingError(error.localizedDescription)
        }
        
        return try await performRequest(request)
    }
    
    /// Performs a PUT request
    /// - Parameters:
    ///   - endpoint: The API endpoint
    ///   - body: The request body to encode
    /// - Returns: Decoded response object
    func put<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        guard let url = buildURL(endpoint: endpoint) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        do {
            request.httpBody = try encoder.encode(body)
        } catch {
            throw NetworkError.encodingError(error.localizedDescription)
        }
        
        return try await performRequest(request)
    }
    
    /// Performs a DELETE request
    /// - Parameter endpoint: The API endpoint
    func delete(_ endpoint: String) async throws {
        guard let url = buildURL(endpoint: endpoint) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        let (_, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError(httpResponse.statusCode, nil)
        }
    }
    
    // MARK: - Private Methods
    
    /// Builds a complete URL from endpoint and optional query items
    private func buildURL(endpoint: String, queryItems: [URLQueryItem]? = nil) -> URL? {
        var components = URLComponents(string: baseURL + endpoint)
        components?.queryItems = queryItems
        return components?.url
    }
    
    /// Performs the network request and decodes the response
    private func performRequest<T: Decodable>(_ request: URLRequest) async throws -> T {
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.invalidResponse
            }
            
            guard (200...299).contains(httpResponse.statusCode) else {
                let errorMessage = String(data: data, encoding: .utf8)
                throw NetworkError.serverError(httpResponse.statusCode, errorMessage)
            }
            
            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw NetworkError.decodingError(error.localizedDescription)
            }
            
        } catch let error as NetworkError {
            throw error
        } catch {
            throw NetworkError.networkFailure(error)
        }
    }
}

// MARK: - Preview Helpers

extension NetworkService {
    /// Creates a mock service for previews and testing
    static func mock() -> NetworkService {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        let session = URLSession(configuration: configuration)
        return NetworkService(session: session)
    }
}

/// URLProtocol for mocking network responses in previews
class MockURLProtocol: URLProtocol {
    static var mockData: Data?
    static var mockResponse: HTTPURLResponse?
    static var mockError: Error?
    
    override class func canInit(with request: URLRequest) -> Bool {
        return true
    }
    
    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        return request
    }
    
    override func startLoading() {
        if let error = MockURLProtocol.mockError {
            client?.urlProtocol(self, didFailWithError: error)
        } else {
            if let response = MockURLProtocol.mockResponse {
                client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            }
            if let data = MockURLProtocol.mockData {
                client?.urlProtocol(self, didLoad: data)
            }
            client?.urlProtocolDidFinishLoading(self)
        }
    }
    
    override func stopLoading() {}
}
