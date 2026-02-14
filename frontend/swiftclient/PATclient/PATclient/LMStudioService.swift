import Foundation
import SwiftUI
import Combine

// MARK: - LM Studio Service
/// Service for communicating with LM Studio's OpenAI-compatible API
/// Supports models like GLM-4.6v-flash
class LMStudioService {
    static let shared = LMStudioService()

    private let baseURL: String
    private let session: URLSession
    private let defaultModel = "GLM-4.6v-flash"

    private init(baseURL: String = Config.lmStudioBaseURL) {
        self.baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        config.timeoutIntervalForResource = 300
        self.session = URLSession(configuration: config)
    }

    // MARK: - Model Management

    struct LMStudioModel: Codable, Identifiable {
        let id: String
        let object: String
        let ownedBy: String?

        enum CodingKeys: String, CodingKey {
            case id, object
            case ownedBy = "owned_by"
        }
    }

    struct ModelsResponse: Codable {
        let object: String
        let data: [LMStudioModel]
    }

    func listModels() async throws -> [LMStudioModel] {
        guard let url = URL(string: "\(baseURL)/models") else {
            throw LLMError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw LLMError.serverError(-1)
            }

            guard httpResponse.statusCode == 200 else {
                throw LLMError.serverError(httpResponse.statusCode)
            }

            return try JSONDecoder().decode(ModelsResponse.self, from: data).data
        } catch let error as LLMError {
            throw error
        } catch {
            throw LLMError.networkError(error)
        }
    }

    // MARK: - Chat Completion

    struct ChatCompletionRequest: Codable {
        let model: String
        let messages: [Message]
        let temperature: Double
        let maxTokens: Int?
        let stream: Bool

        enum CodingKeys: String, CodingKey {
            case model, messages, temperature
            case maxTokens = "max_tokens"
            case stream
        }

        struct Message: Codable {
            let role: String
            let content: String
        }
    }

    struct ChatCompletionResponse: Codable {
        let id: String
        let object: String
        let created: Int
        let model: String
        let choices: [Choice]
        let usage: Usage?

        struct Choice: Codable {
            let index: Int
            let message: Message
            let finishReason: String?

            enum CodingKeys: String, CodingKey {
                case index, message
                case finishReason = "finish_reason"
            }
        }

        struct Message: Codable {
            let role: String
            let content: String
        }

        struct Usage: Codable {
            let promptTokens: Int
            let completionTokens: Int
            let totalTokens: Int

            enum CodingKeys: String, CodingKey {
                case promptTokens = "prompt_tokens"
                case completionTokens = "completion_tokens"
                case totalTokens = "total_tokens"
            }
        }
    }

    func chatCompletion(
        messages: [Message],
        model: String = "GLM-4.6v-flash",
        temperature: Double = 0.7,
        maxTokens: Int? = nil
    ) async throws -> String {
        guard let url = URL(string: "\(baseURL)/chat/completions") else {
            throw LLMError.invalidURL
        }

        let apiMessages = messages.map { msg in
            let role: String
            switch msg.type {
            case .user: role = "user"
            case .assistant: role = "assistant"
            case .system: role = "system"
            }
            return ChatCompletionRequest.Message(role: role, content: msg.content)
        }

        let request = ChatCompletionRequest(
            model: model,
            messages: apiMessages,
            temperature: temperature,
            maxTokens: maxTokens,
            stream: false
        )

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        do {
            let (data, response) = try await session.data(for: urlRequest)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw LLMError.serverError(-1)
            }

            guard httpResponse.statusCode == 200 else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("LM Studio error: \(errorString)")
                }
                throw LLMError.serverError(httpResponse.statusCode)
            }

            let completionResponse = try JSONDecoder().decode(ChatCompletionResponse.self, from: data)
            return completionResponse.choices.first?.message.content ?? ""
        } catch let error as LLMError {
            throw error
        } catch {
            throw LLMError.decodingError(error)
        }
    }

    // MARK: - Health Check

    func checkHealth() async -> Bool {
        guard let url = URL(string: "\(baseURL)/models") else { return false }
        do {
            let (_, response) = try await session.data(from: url)
            guard let httpResponse = response as? HTTPURLResponse else { return false }
            return httpResponse.statusCode == 200
        } catch {
            print("LM Studio not reachable: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Query Agent
    /// Send a query to the Agent service using LM Studio as the LLM provider
    func query(
        text: String,
        webSearch: Bool = false,
        useMemory: Bool = true,
        userId: String = "default"
    ) async throws -> QueryResponse {
        return try await AgentService.shared.query(
            text: text,
            webSearch: webSearch,
            useMemory: useMemory,
            userId: userId,
            stream: false,
            llmProvider: "lmstudio"
        )
    }
}

// MARK: - Provider Type
enum LLMProvider: String, CaseIterable, Identifiable {
    case ollama = "ollama"
    case lmstudio = "lmstudio"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .ollama: return "Ollama"
        case .lmstudio: return "LM Studio"
        }
    }

    var icon: String {
        switch self {
        case .ollama: return "cpu"
        case .lmstudio: return "desktopcomputer"
        }
    }
}

// MARK: - Unified LLM Service
/// Unified service that works with both Ollama and LM Studio
class UnifiedLLMService {
    static let shared = UnifiedLLMService()

    @Published var selectedProvider: LLMProvider = .lmstudio
    @Published var availableModels: [String] = []
    @Published var selectedModel: String = "GLM-4.6v-flash"
    @Published var isLoadingModels: Bool = false
    @Published var status: ServiceStatus = .disconnected

    private init() {}

    /// Check health based on selected provider
    func checkHealth() async -> Bool {
        switch selectedProvider {
        case .ollama:
            do {
                _ = try await LLMService.shared.listModels()
                await MainActor.run { self.status = .healthy }
                return true
            } catch {
                await MainActor.run { self.status = .disconnected }
                return false
            }
        case .lmstudio:
            let isHealthy = await LMStudioService.shared.checkHealth()
            await MainActor.run { self.status = isHealthy ? .healthy : .disconnected }
            return isHealthy
        }
    }

    /// Load available models based on selected provider
    func loadAvailableModels() async {
        await MainActor.run { isLoadingModels = true }

        switch selectedProvider {
        case .ollama:
            do {
                let models = try await LLMService.shared.listModels()
                let modelNames = models.map { $0.name }
                await MainActor.run {
                    availableModels = modelNames
                    if !modelNames.isEmpty && !modelNames.contains(selectedModel) {
                        selectedModel = modelNames.first ?? "llama3"
                    }
                    isLoadingModels = false
                }
            } catch {
                await MainActor.run { isLoadingModels = false }
            }
        case .lmstudio:
            do {
                let models = try await LMStudioService.shared.listModels()
                let modelNames = models.map { $0.id }
                await MainActor.run {
                    availableModels = modelNames
                    if !modelNames.isEmpty && !modelNames.contains(selectedModel) {
                        selectedModel = modelNames.first ?? "GLM-4.6v-flash"
                    }
                    isLoadingModels = false
                }
            } catch {
                // Fallback to default model
                await MainActor.run {
                    availableModels = ["GLM-4.6v-flash"]
                    selectedModel = "GLM-4.6v-flash"
                    isLoadingModels = false
                }
            }
        }
    }

    /// Send a chat completion request
    func chatCompletion(messages: [Message]) async throws -> String {
        switch selectedProvider {
        case .ollama:
            // Use existing AgentService which routes through backend
            return try await AgentService.shared.query(
                text: messages.last?.content ?? "",
                webSearch: false,
                useMemory: true,
                userId: "default",
                stream: false
            ).response
        case .lmstudio:
            return try await LMStudioService.shared.chatCompletion(
                messages: messages,
                model: selectedModel
            )
        }
    }
}
