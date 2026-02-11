//
//  FileService.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//


//
//  FileService.swift
//  PATclient
//
//  Service for file operations and markdown export
//

 import Foundation
 import AppKit
 import UniformTypeIdentifiers

class FileService {
    static let shared = FileService()
    
    private init() {}
    
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
        
        let shouldStopAccess = url.startAccessingSecurityScopedResource()
        defer {
            if shouldStopAccess {
                url.stopAccessingSecurityScopedResource()
            }
        }
        
        // Create export dictionary directly
        let exportData: [String: Any] = [
            "title": sessionTitle,
            "exportedAt": Date().timeIntervalSince1970,
            "messages": messages.map { ["type": $0.type.rawValue, "content": $0.content, "timestamp": $0.timestamp.timeIntervalSince1970] },
            "settings": [
                "useWebSearch": settings.useWebSearch,
                "useMemoryContext": settings.useMemoryContext,
                "llmProvider": settings.llmProvider,
                "selectedModel": settings.selectedModel,
                "temperature": settings.temperature,
                "maxTokens": settings.maxTokens,
                "useDarkMode": settings.useDarkMode
            ]
        ]
        
        let data = try JSONSerialization.data(withJSONObject: exportData, options: [.prettyPrinted, .sortedKeys])
        try data.write(to: url)
        
        return url
    }
    
    func selectFileToUpload() throws -> URL {
        let openPanel = NSOpenPanel()
        openPanel.allowedContentTypes = [.plainText, .pdf, .text]
        openPanel.allowsMultipleSelection = false
        openPanel.canChooseDirectories = false
        openPanel.canChooseFiles = true
        openPanel.title = "Select Document to Upload"
        openPanel.prompt = "Upload"
        
        let response = openPanel.runModal()
        guard response == .OK, let url = openPanel.url else {
            throw FileError.userCancelled
        }
        
        return url
    }
    
    func readContent(from url: URL) throws -> String {
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
