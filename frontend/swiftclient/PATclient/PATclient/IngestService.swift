//
//  IngestService.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import Foundation
import os.log
import SwiftUI

class IngestService {
    static let shared = IngestService()
    
    private let baseURL: String
    private let session: URLSession
    private let logger = SharedLogger.shared
    private init(baseURL: String = Config.ingestBaseURL) {
            self.baseURL = baseURL
            let config = URLSessionConfiguration.default
            config.timeoutIntervalForRequest = 60
            config.timeoutIntervalForResource = 300
            self.session = URLSession(configuration: config)
            
    
        logger.general.info("IngestService initialized with baseURL: \(baseURL)")
    }
    
    // MARK: - Resume Upload
    func uploadResume(filePath: String, metadata: [String: Any]) async throws -> UploadResponse {
        let endpoint = "\(baseURL)/upload"
        logger.ingest.info("Starting resume upload for: \(filePath)")
        
        guard let url = URL(string: endpoint) else {
            logger.ingest.error("Invalid URL: \(endpoint)")
            throw IngestError.invalidURL
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        
        let boundary = "Boundary-\(UUID().uuidString)"
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add file part
        guard let fileData = try? Data(contentsOf: URL(fileURLWithPath: filePath)) else {
            logger.ingest.error("Failed to read file: \(filePath)")
            throw IngestError.fileReadError
        }
        
        let fileName = URL(fileURLWithPath: filePath).lastPathComponent
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n".data(using: .utf8)!)
        
        // Add metadata part
        if let metadataData = try? JSONSerialization.data(withJSONObject: metadata) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"metadata\"\r\n\r\n".data(using: .utf8)!)
            body.append(metadataData)
            body.append("\r\n".data(using: .utf8)!)
        }
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        urlRequest.httpBody = body
        
        let startTime = Date()
        
        do {
            let (data, response) = try await session.data(for: urlRequest)
            let responseTime = Date().timeIntervalSince(startTime)
            
            logger.logNetworkResponse(endpoint, statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0, responseTime: responseTime)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                let error = IngestError.invalidResponse
                logger.logError(error, context: "Invalid HTTP response")
                throw error
            }
            
            logger.ingest.info("HTTP Status: \(httpResponse.statusCode)")
            
            guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
                let error = IngestError.serverError(httpResponse.statusCode)
                
                if let errorString = String(data: data, encoding: .utf8) {
                    logger.ingest.error("Upload error response: \(errorString)")
                }
                
                logger.logError(error, context: "Upload returned non-2xx status")
                throw error
            }
            
            do {
                let uploadResponse = try JSONDecoder().decode(UploadResponse.self, from: data)
                logger.ingest.info("Resume upload successful. Document ID: \(uploadResponse.document_id ?? "unknown")")
                return uploadResponse
            } catch {
                logger.logError(error, context: "JSON decoding upload response")
                throw error
            }
            
        } catch {
            logger.logError(error, context: "Network request failed")
            throw error
        }
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
    func ingestDocument(filename: String, content: String, metadata: [String: Any]? = nil) async throws -> IngestResponse {
        let endpoint = "\(baseURL)/ingest"
        logger.ingest.info("Starting document ingestion for: \(filename)")
        logger.logNetworkRequest(endpoint, method: "POST", body: "Content length: \(content.count)")
        
        guard let url = URL(string: endpoint) else {
            logger.ingest.error("Invalid URL: \(endpoint)")
            throw IngestError.invalidURL
        }
        
        var body: [String: Any] = [
            "filename": filename,
            "content": content
        ]
        
        if let metadata = metadata {
            body["metadata"] = metadata
        }
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            urlRequest.httpBody = try JSONSerialization.data(withJSONObject: body)
            logger.ingest.debug("JSON serialization successful")
        } catch {
            logger.logError(error, context: "JSON serialization for ingest")
            throw IngestError.encodingError
        }
        
        let startTime = Date()
        
        do {
            let (data, response) = try await session.data(for: urlRequest)
            let responseTime = Date().timeIntervalSince(startTime)
            
            logger.logNetworkResponse(endpoint, statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0, responseTime: responseTime)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                let error = IngestError.invalidResponse
                logger.logError(error, context: "Invalid HTTP response")
                throw error
            }
            
            logger.ingest.info("HTTP Status: \(httpResponse.statusCode)")
            
            guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
                let error = IngestError.serverError(httpResponse.statusCode)
                
                // Try to get more error details from response
                if let errorString = String(data: data, encoding: .utf8) {
                    logger.ingest.error("Server error response: \(errorString)")
                }
                
                logger.logError(error, context: "Server returned non-2xx status")
                throw error
            }
            
            do {
                let ingestResponse = try JSONDecoder().decode(IngestResponse.self, from: data)
                logger.ingest.info("Ingestion successful. Document ID: \(ingestResponse.document_id ?? "unknown")")
                return ingestResponse
            } catch {
                logger.logError(error, context: "JSON decoding ingest response")
                throw error
            }
            
        } catch {
            logger.logError(error, context: "Network request failed")
            throw error
        }
    }
    
    func searchDocuments(query: String, topK: Int = 5) async throws -> [Source] {
        let endpoint = "\(baseURL)/search"
        logger.ingest.info("Searching documents with query: \(query.prefix(100))...")
        logger.logNetworkRequest(endpoint, method: "POST", body: "Query: \(query), topK: \(topK)")
        
        guard let url = URL(string: endpoint) else {
            logger.ingest.error("Invalid URL: \(endpoint)")
            throw IngestError.invalidURL
        }
        
        let requestBody = [
            "query": query,
            "top_k": topK
        ] as [String: Any]
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            urlRequest.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            logger.logError(error, context: "JSON serialization for search")
            throw IngestError.encodingError
        }
        
        let startTime = Date()
        
        do {
            let (data, response) = try await session.data(for: urlRequest)
            let responseTime = Date().timeIntervalSince(startTime)
            
            logger.logNetworkResponse(endpoint, statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0, responseTime: responseTime)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                let error = IngestError.invalidResponse
                if let errorString = String(data: data, encoding: .utf8) {
                    logger.ingest.error("Search failed response: \(errorString)")
                }
                logger.logError(error, context: "Search request failed")
                throw error
            }
            
            do {
                let sources = try JSONDecoder().decode([Source].self, from: data)
                logger.ingest.info("Search successful. Found \(sources.count) sources")
                return sources
            } catch {
                logger.logError(error, context: "JSON decoding search response")
                throw error
            }
            
        } catch {
            logger.logError(error, context: "Search request failed")
            throw error
        }
    }
    
    func listResumes() async throws -> [Document] {
        let endpoint = "\(baseURL)/resumes"
        logger.ingest.info("Listing resumes")
        logger.logNetworkRequest(endpoint, method: "GET")
        
        guard let url = URL(string: endpoint) else {
            logger.ingest.error("Invalid URL: \(endpoint)")
            throw IngestError.invalidURL
        }
        
        let startTime = Date()
        
        do {
            let (data, response) = try await session.data(from: url)
            let responseTime = Date().timeIntervalSince(startTime)
            
            logger.logNetworkResponse(endpoint, statusCode: (response as? HTTPURLResponse)?.statusCode ?? 0, responseTime: responseTime)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                let error = IngestError.invalidResponse
                logger.logError(error, context: "List resumes failed")
                throw error
            }
            
            do {
                let resumeResponse = try JSONDecoder().decode(ResumeListResponse.self, from: data)
                logger.ingest.info("Found \(resumeResponse.resumes.count) resumes")
                return resumeResponse.resumes
            } catch {
                logger.logError(error, context: "JSON decoding resume list")
                throw error
            }
            
        } catch {
            logger.logError(error, context: "List resumes request failed")
            throw error
        }
    }
}

struct IngestResponse: Codable {
    let status: String
    let message: String
    let document_id: String?
}

struct ResumeListResponse: Codable {
    let resumes: [Document]
}

struct Document: Codable {
    let id: UUID
    let filename: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case filename
    }
}

enum IngestError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case fileReadError
    case encodingError
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .serverError(let code):
            return "Server error: \(code)"
        case .fileReadError:
            return "Failed to read file"
        case .encodingError:
            return "Failed to encode data"
        }
    }
}
