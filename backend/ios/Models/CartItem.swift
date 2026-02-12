import Foundation

struct CartItem: Codable {
    let productId: Int
    let quantity: Int
    
    enum CodingKeys: String, CodingKey {
        case productId = "product_id", quantity
    }
}