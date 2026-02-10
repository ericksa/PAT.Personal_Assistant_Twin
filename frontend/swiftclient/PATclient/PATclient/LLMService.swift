import Foundation

// MARK: - Model Types
struct OllamaModel: Codable, Identifiable {
    let name: String
    let model: String
    let modified_at: String?
    let size: Int64?
    let digest: String?
    let details: ModelDetails?
    let expires_at: String?
    
    var id: String { name }
}

struct ModelDetails: Codable {
    let format: String?
    let family: String?
    let families: [String]?
    let parameter_size: String?
    let quantization_level: String?
}

struct OllamaModelsResponse: Codable {
    let models: [OllamaModel]
}

// MARK: - Error Types
enum LLMError: Error, LocalizedError {
    case invalidURL
    case serverError(Int)
    case networkError(Error)
    case decodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
    }
}

// MARK: - LLM Service
class LLMService {
    static let shared = LLMService()
    
    private let baseURL: String
    private let session: URLSession
    
    private init(baseURL: String = Config.ollamaBaseURL) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
    }
    
    func listModels() async throws -> [OllamaModel] {
        guard let url = URL(string: "\(baseURL)/api/tags") else {
            throw LLMError.invalidURL
        }
        
        do {
            let (data, response) = try await session.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw LLMError.serverError(-1)
            }
            
            guard httpResponse.statusCode == 200 else {
                throw LLMError.serverError(httpResponse.statusCode)
            }
            
            return try JSONDecoder().decode(OllamaModelsResponse.self, from: data).models
        } catch let error as LLMError {
            throw error
        } catch {
            throw LLMError.networkError(error)
        }
    }
}

