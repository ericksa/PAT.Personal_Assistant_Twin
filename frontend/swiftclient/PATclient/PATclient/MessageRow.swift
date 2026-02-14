//
//  MessageRow.swift
//  PATclient
//
//  Created by Adam Erickson on 1/22/26.
//

import SwiftUI

struct MessageRow: View {
    let message: Message
    let viewModel: ChatViewModel  // ✅ Added viewModel parameter
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            avatarView
                .padding(.top, 4)
            
            VStack(alignment: .leading, spacing: 6) {
                messageHeader
                
                messageContent
                    .padding(.vertical, 8)
                    .padding(.horizontal, 12)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(message.type == .user ? Color.blue.opacity(0.1) : Color.green.opacity(0.1))
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                
                if !message.sources.isEmpty {
                    sourcesView
                }
                
                if !message.toolsUsed.isEmpty {
                    toolsView
                }
                
                footerView
            }
            .padding(.vertical, 2)
        }
        .padding(.horizontal, 16)
    }
    
    @ViewBuilder
    private var avatarView: some View {
        ZStack {
            Circle()
                .fill(avatarColor)
                .frame(width: 36, height: 36)
            
            Text(avatarEmoji)
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.white)
        }
    }
    
    @ViewBuilder
    private var messageHeader: some View {
        HStack(spacing: 8) {
            Text(messageHeaderTitle)
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
            
            if message.type == .assistant {
                if !message.modelUsed.isEmpty {
                    Text("• \(message.modelUsed)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                if message.processingTime > 0 {
                    Text("• \(String(format: "%.2f", message.processingTime))s")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            Text(message.timestamp, style: .time)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    @ViewBuilder
    private var messageContent: some View {
        Text(message.content)
            .font(.body)
            .foregroundColor(.primary)
            .textSelection(.enabled)
            .lineSpacing(4)
            .fixedSize(horizontal: false, vertical: true)
    }
    
    @ViewBuilder
    private var sourcesView: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Sources:")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(.secondary)
            
            ForEach(message.sources) { source in
                HStack(spacing: 6) {
                    Image(systemName: sourceIcon(for: source))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    if let url = source.url, !url.isEmpty,
                       let nsURL = URL(string: url) {
                        Link(source.displayName, destination: nsURL)
                            .font(.caption)
                            .foregroundColor(.blue)
                            .underline()
                    } else {
                        Text(source.displayName)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    if let score = source.score {
                        Text(String(format: "%.2f", score))
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .padding(.top, 8)
    }
    
    @ViewBuilder
    private var toolsView: some View {
        HStack(spacing: 6) {
            Image(systemName: "wrench.and.screwdriver")
                .font(.caption2)
                .foregroundColor(.secondary)
            
            Text("Tools: \(message.toolsUsed.joined(separator: ", "))")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.top, 4)
    }
    
    @ViewBuilder
    private var footerView: some View {
        HStack(spacing: 8) {
            if message.type == .assistant {
                Button(action: {
                    // Regenerate this message
                    Task { await viewModel.regenerateLastResponse() }
                }) {
                    Image(systemName: "arrow.clockwise")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.top, 2)
    }
    
    private var avatarColor: Color {
        switch message.type {
        case .user:
            return .blue
        case .assistant:
            return .green
        case .system:
            return .gray
        }
    }
    
    private var avatarEmoji: String {
        switch message.type {
        case .user:
            return "👤"
        case .assistant:
            return "🤖"
        case .system:
            return "⚙️"
        }
    }
    
    private var messageHeaderTitle: String {
        switch message.type {
        case .user:
            return "You"
        case .assistant:
            return "PAT"
        case .system:
            return "System"
        }
    }
    
    private func sourceIcon(for source: Source) -> String {
        // Determine icon based on source properties
        if let url = source.url, !url.isEmpty {
            return "globe"
        } else if source.filename != nil {
            return "doc.text"
        }
        return "questionmark.circle"
    }
}

#Preview {
    let viewModel = ChatViewModel()  // ✅ Create viewModel for preview
    
    VStack(spacing: 0) {
        MessageRow(message: Message(
            type: .user,
            content: "What is the current weather in San Francisco?",
            timestamp: Date()
        ), viewModel: viewModel)
        
        Divider()
        
        MessageRow(message: Message(
            type: .assistant,
            content: "Based on current information, the weather in San Francisco is typically around 60-70°F during the day.",
            timestamp: Date(),
            sources: [
                Source(url: "https://weather.com", title: "Weather.com", source: "web", score: 0.95),
                Source(filename: "sf_weather_notes.txt", content: "Weather notes...",  source: "document", score: 0.87)
            ],
            toolsUsed: ["web"],
            modelUsed: "llama2",
            processingTime: 2.34
        ), viewModel: viewModel)
    }
}

