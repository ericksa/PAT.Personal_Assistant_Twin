import Foundation

protocol Networking {
    func request<T: Codable>(url: String, method: HTTPMethod, parameters: [String: Any]?, completion: @escaping (Result<T, Error>) -> Void)
}

extension Networking {
    func request<T: Codable>(url: String, method: HTTPMethod = .get, parameters: [String: Any]? = nil, completion: @escaping (Result<T, Error>) -> Void) {
        NetworkManager.shared.request(url: url, method: method, parameters: parameters, completion: completion)
    }
}