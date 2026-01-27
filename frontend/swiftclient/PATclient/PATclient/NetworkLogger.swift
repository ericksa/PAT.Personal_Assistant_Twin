import Foundation
import os.log

class NetworkLogger {
    static let shared = NetworkLogger()
    private let logger = SharedLogger.shared
    
    private init() {}
    
    func logRequest(_ request: URLRequest) {
        guard let url = request.url?.absoluteString else { return }
        let method = request.httpMethod ?? "GET"
        
        var headers: [String: String] = [:]
        request.allHTTPHeaderFields?.forEach { key, value in
            // Don't log sensitive headers
            if !["Authorization", "Cookie", "Set-Cookie"].contains(key) {
                headers[key] = value
            }
        }
        
        logger.network.info("🌐 \(method) \(url)")
        logger.general.debug("Headers: \(headers)")
        
        if let body = request.httpBody,
           let bodyString = String(data: body, encoding: .utf8),
           bodyString.count < 1000 { // Only log small bodies
            logger.general.debug("Body: \(bodyString)")
        }
    }
    
    func logResponse(_ response: URLResponse?, data: Data?, error: Error?) {
        if let error = error {
            logger.network.error("❌ Network Error: \(error.localizedDescription)")
            return
        }
        
        guard let httpResponse = response as? HTTPURLResponse else {
            logger.network.error("❌ Invalid response")
            return
        }
        
        let emoji = httpResponse.statusCode < 300 ? "✅" : httpResponse.statusCode < 400 ? "➡️" : "❌"
        logger.network.info("\(emoji) HTTP \(httpResponse.statusCode)")
        
        if let data = data, data.count < 1000 {
            if let responseString = String(data: data, encoding: .utf8) {
                logger.general.debug("Response: \(responseString.replacingOccurrences(of: "\n", with: "\\n"))")
            }
        }
    }
}
