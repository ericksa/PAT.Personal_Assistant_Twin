//
//  Source.swift
//  PATclient
//
//  Source model for document references
//

import Foundation

enum SourceType {
    case document
    case web
    case unknown
}

struct Source: Identifiable, Codable, Hashable {
    let id: UUID
    var filename: String?
    var content: String?
    var url: String?
    var title: String?
    var source: String?
    var score: Double?
    
    init(id: UUID = UUID(), filename: String? = nil, content: String? = nil, url: String? = nil, title: String? = nil, source: String? = nil, score: Double? = nil) {
        self.id = id
        self.filename = filename
        self.content = content
        self.url = url
        self.title = title
        self.source = source
        self.score = score
    }
    
    var sourceType: SourceType {
        if let source = source?.lowercased() {
            if source.contains("web") || source.contains("duckduckgo") || source.contains("google") {
                return .web
            } else if source.contains("local") || source.contains("document") {
                return .document
            }
        }
        if url != nil {
            return .web
        }
        return .document
    }
    
    var displayName: String {
        if let title = title, !title.isEmpty {
            return title
        }
        if let filename = filename, !filename.isEmpty {
            return filename
        }
        if let url = url, !url.isEmpty {
            return URL(string: url)?.host ?? url
        }
        return "Unknown Source"
    }
}
