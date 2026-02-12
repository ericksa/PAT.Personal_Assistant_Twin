import Foundation

struct Product: Codable {
    let id: Int
    let name: String
    let description: String
    let price: Double
    let category: String
    let image: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, description, price, category, image
    }
}