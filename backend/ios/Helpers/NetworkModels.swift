import Foundation

struct Response<T: Codable>: Codable {
    let data: T
    let success: Bool
    let message: String?
    
    private enum CodingKeys: String, CodingKey {
        case data, success, message
    }
}

struct ErrorResponse: Codable {
    let success: Bool
    let message: String
    
    private enum CodingKeys: String, CodingKey {
        case success, message
    }
}