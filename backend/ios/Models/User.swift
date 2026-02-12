import Foundation

struct User: Codable {
    let id: Int
    let name: String
    let email: String
    let role: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, email, role
    }
}