//
//  FileService.swift
//  PATclient
//
//  Service for file operations and markdown export
//

import Foundation
import AppKit
internal import UniformTypeIdentifiers

class FileService {
    static let shared = FileService()
    
    private init() {}
    
    // MARK: - Export Methods (MainActor required for NSSavePanel)
    
    @MainActor
    func exportChatAsMarkdown(messages: [Message], sessionTitle: String) throws -> URL {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [.plainText]
        savePanel.nameFieldStringValue = "\(sessionTitle.sanitizedFilename()).md"
        savePanel.title = "Export Chat as Markdown"
        savePanel.prompt = "Save"
        
        let response = savePanel.runModal()
        guard response == .OK, let url = savePanel.url else {
            throw FileError.userCancelled
        }
        
        let markdownContent = generateMarkdown(from: messages, sessionTitle: sessionTitle)
        try markdownContent.write(to: url, atomically: true, encoding: .utf8)
        
        return url
    }
    
    @MainActor
    func exportChatAsJSON(messages: [Message], sessionTitle: String, settings: ChatSettings) throws -> URL {
        let savePanel = NSSavePanel()
        savePanel.allowedContentTypes = [.json]
        savePanel.nameFieldStringValue = "\(sessionTitle.sanitizedFilename()).json"
        savePanel.title = "Export Chat as JSON"
        savePanel.prompt = "Save"
        
        let response = savePanel.runModal()
        guard response == .OK, let url = savePanel.url else {
            throw FileError.userCancelled
        }
        
        let exportData = ChatExport(
            title: sessionTitle,
            exportedAt: Date(),
            messages: messages,
            settings: settings
        )
        
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(exportData)
        try data.write(to: url)
        
        return url
    }
    
    // MARK: - Upload Method (MainActor required for NSOpenPanel)
    
    @MainActor
    func selectFileToUpload() throws -> URL {
        let openPanel = NSOpenPanel()
        openPanel.allowedContentTypes = [.plainText, .pdf, .text, .utf8PlainText, .utf16PlainText]
        openPanel.allowsMultipleSelection = false
        openPanel.canChooseDirectories = false
        openPanel.canChooseFiles = true
        openPanel.title = "Select Document to Upload"
        openPanel.prompt = "Upload"
        
        // Ensure we're properly modal to the key window
        if let keyWindow = NSApplication.shared.keyWindow {
            openPanel.beginSheetModal(for: keyWindow) { response in
                // Handle via continuation if needed, but runModal() is simpler for now
            }
        }
        
        let response = openPanel.runModal()
        guard response == .OK, let url = openPanel.url else {
            throw FileError.userCancelled
        }
        
        // Security-scoped resource handling for sandboxed apps
        guard url.startAccessingSecurityScopedResource() else {
            throw FileError.fileReadError
        }
        defer { url.stopAccessingSecurityScopedResource() }
        
        return url
    }
    
    func readContent(from url: URL) throws -> String {
        // Re-access security scoped resource if needed
        guard url.startAccessingSecurityScopedResource() else {
            // If it fails, try anyway - might not be sandboxed
            return try String(contentsOf: url, encoding: .utf8)
        }
        defer { url.stopAccessingSecurityScopedResource() }
        
        return try String(contentsOf: url, encoding: .utf8)
    }
    
    private func generateMarkdown(from messages: [Message], sessionTitle: String) -> String {
        var markdown = "# \(sessionTitle)\n\n"
        markdown += "Exported: \(DateFormatter.localizedString(from: Date(), dateStyle: .medium, timeStyle: .short))\n\n"
        markdown += "---\n\n"
        
        for message in messages {
            switch message.type {
            case .user:
                markdown += "## 👤 User\n\n"
            case .assistant:
                markdown += "## 🤖 Assistant"
                if !message.modelUsed.isEmpty {
                    markdown += " *(\(message.modelUsed))*"
                }
                if message.processingTime > 0 {
                    markdown += " *(\(String(format: "%.2f", message.processingTime))s)*"
                }
                markdown += "\n\n"
            case .system:
                markdown += "## ⚙️ System\n\n"
            }
            
            markdown += "\(message.content)\n\n"
            
            if !message.sources.isEmpty {
                markdown += "**Sources:**\n"
                for (index, source) in message.sources.enumerated() {
                    markdown += "\(index + 1). "
                    if let url = source.url {
                        markdown += "[\(source.displayName)](\(url))"
                    } else {
                        markdown += source.displayName
                    }
                    if let score = source.score {
                        markdown += " *(score: \(String(format: "%.3f", score)))*"
                    }
                    markdown += "\n"
                }
                markdown += "\n"
            }
            
            if !message.toolsUsed.isEmpty {
                markdown += "**Tools used:** \(message.toolsUsed.joined(separator: ", "))\n\n"
            }
            
            markdown += "---\n\n"
        }
        
        return markdown
    }
}

struct ChatExport: Codable {
    let title: String
    let exportedAt: Date
    let messages: [Message]
    let settings: ChatSettings
}

enum FileError: Error, LocalizedError {
    case userCancelled
    case fileReadError
    case fileWriteError
    case invalidFileFormat
    
    var errorDescription: String? {
        switch self {
        case .userCancelled:
            return "Operation cancelled by user"
        case .fileReadError:
            return "Failed to read file"
        case .fileWriteError:
            return "Failed to write file"
        case .invalidFileFormat:
            return "Invalid file format"
        }
    }
}

extension String {
    func sanitizedFilename() -> String {
        let invalidCharacters = CharacterSet(charactersIn: ":/\\?*|\"<>")
        return components(separatedBy: invalidCharacters).joined(separator: "_")
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: " ", with: "_")
    }
}
