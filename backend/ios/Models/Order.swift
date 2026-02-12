import Foundation

struct Order: Codable {
    let id: Int
    let userId: Int
    let total: Double
    let status: String
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, userId = "user_id", total, status, createdAt = "created_at"
    }
}