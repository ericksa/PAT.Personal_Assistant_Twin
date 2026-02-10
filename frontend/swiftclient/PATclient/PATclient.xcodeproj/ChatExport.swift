struct ChatExport: Codable {
    let title: String
    let exportedAt: Date
    let messages: [Message]
    let settings: ChatSettings
}
