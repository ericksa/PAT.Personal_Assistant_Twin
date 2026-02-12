import Foundation

class NetworkManager {
    static let shared = NetworkManager()
    
    private init() {}
    
    func request<T: Codable>(url: String, method: HTTPMethod = .get, parameters: [String: Any]? = nil, completion: @escaping (Result<T, Error>) -> Void) {
        guard let url = URL(string: url) else {
            completion(.failure(NSError(domain: "NetworkManager", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        
        if let parameters = parameters, method != .get {
            request.httpBody = try? JSONSerialization.data(withJSONObject: parameters, options: [])
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "NetworkManager", code: -2, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                return
            }
            
            do {
                let decoded = try JSONDecoder().decode(T.self, from: data)
                completion(.success(decoded))
            } catch {
                completion(.failure(error))
            }
        }
        
        task.resume()
    }
}

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case delete = "DELETE"
    case patch = "PATCH"
}