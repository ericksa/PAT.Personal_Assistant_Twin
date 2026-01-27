//
//  SessionService.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//


//
//  SessionService.swift
//  PATclient
//
//  Service for managing chat sessions
//

import Foundation

class SessionService {
    static let shared = SessionService()
    
    private let fileManager = FileManager.default
    private let sessionsDirectory: URL
    
    private init() {
        let applicationSupport = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let appDirectory = applicationSupport.appendingPathComponent("PATclient", isDirectory: true)
        self.sessionsDirectory = appDirectory.appendingPathComponent("Sessions", isDirectory: true)
        
        createDirectoryIfNeeded(at: appDirectory)
        createDirectoryIfNeeded(at: sessionsDirectory)
    }
    
    private func createDirectoryIfNeeded(at url: URL) {
        if !fileManager.fileExists(atPath: url.path) {
            try? fileManager.createDirectory(at: url, withIntermediateDirectories: true)
        }
    }
    
    func saveSession(_ session: ChatSession) throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(session)
        
        let fileURL = sessionsDirectory.appendingPathComponent("\(session.id.uuidString).json")
        try data.write(to: fileURL)
    }
    
    func loadSession(id: UUID) throws -> ChatSession {
        let fileURL = sessionsDirectory.appendingPathComponent("\(id.uuidString).json")
        let data = try Data(contentsOf: fileURL)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(ChatSession.self, from: data)
    }
    
    func loadAllSessions() throws -> [ChatSession] {
        let files = try fileManager.contentsOfDirectory(at: sessionsDirectory, includingPropertiesForKeys: nil)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        var sessions: [ChatSession] = []
        for file in files where file.pathExtension == "json" {
            do {
                let data = try Data(contentsOf: file)
                let session = try decoder.decode(ChatSession.self, from: data)
                sessions.append(session)
            } catch {
                print("Failed to load session from \(file.lastPathComponent): \(error)")
            }
        }
        
        return sessions.sorted { $0.updatedAt > $1.updatedAt }
    }
    
    func deleteSession(id: UUID) throws {
        let fileURL = sessionsDirectory.appendingPathComponent("\(id.uuidString).json")
        try fileManager.removeItem(at: fileURL)
    }
    
    func createNewSession(title: String = "New Chat") -> ChatSession {
        return ChatSession(title: title)
    }
}
