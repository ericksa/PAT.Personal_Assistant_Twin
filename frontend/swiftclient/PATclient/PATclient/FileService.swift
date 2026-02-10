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
        
        let shouldStopAccess = url.startAccessingSecurityScopedResource()
        defer {
            if shouldStopAccess {
                url.stopAccessingSecurityScopedResource()
            }
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
        
        let shouldStopAccess = url.startAccessingSecurityScopedResource()
        defer {
            if shouldStopAccess {
                url.stopAccessingSecurityScopedResource()
            }
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
        openPanel.allowedContentTypes = [.plainText, .utf8PlainText, .utf16PlainText, .text, .pdf]
        openPanel.allowsMultipleSelection = false
        openPanel.canChooseDirectories = false
        openPanel.canChooseFiles = true
        openPanel.title = "Select Document to Upload"
        openPanel.prompt = "Upload"
        openPanel.message = "Select a text or PDF document to upload"
        
        let response = openPanel.runModal()
        guard response == .OK, let url = openPanel.url else {
            throw FileError.userCancelled
        }
        
        return url
    }
    
    func readContent(from url: URL) throws -> String {
        var isStale = false
        let bookmarkData = try url.bookmarkData(
            options: .withSecurityScope,
            includingResourceValuesForKeys: nil,
            relativeTo: nil
        )
        
        let resolvedURL = try URL(
            resolvingBookmarkData: bookmarkData,
            options: .withSecurityScope,
            relativeTo: nil,
            bookmarkDataIsStale: &isStale
        )
        
        guard resolvedURL.startAccessingSecurityScopedResource() else {
            throw FileError.fileReadError
        }
        defer {
            resolvedURL.stopAccessingSecurityScopedResource()
        }
        
        // Try UTF-8 first
        if let content = try? String(contentsOf: resolvedURL, encoding: .utf8) {
            return content
        }
        
        // Try other encodings
        let encodings: [String.Encoding] = [.utf8, .utf16, .isoLatin1, .macOSRoman, .ascii]
        for encoding in encodings {
            if let content = try? String(contentsOf: resolvedURL, encoding: encoding) {
                return content
            }
        }
        
        throw FileError.fileReadError
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

