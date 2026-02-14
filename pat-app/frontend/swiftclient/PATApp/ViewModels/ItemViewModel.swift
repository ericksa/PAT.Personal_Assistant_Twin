//
//  ItemViewModel.swift
//  PATApp
//
//  Created by PAT on 2/13/26.
//

import Foundation
import Combine

// Forward declarations for preview
struct Item: Identifiable, Codable, Equatable {
    let id: UUID
    let name: String
    let description: String?
    let category: String?
    let isActive: Bool
    let createdAt: Date
    
    init(id: UUID = UUID(), name: String, description: String? = nil, category: String? = nil, isActive: Bool = true, createdAt: Date = Date()) {
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.isActive = isActive
        self.createdAt = createdAt
    }
}

struct ItemsResponse: Codable {
    let items: [Item]
    let total: Int
    let skip: Int
    let limit: Int
}

struct CreateItemRequest: Codable {
    let name: String
    let description: String?
    let category: String?
    let isActive: Bool?
}

struct UpdateItemRequest: Codable {
    let name: String?
    let description: String?
    let category: String?
    let isActive: Bool?
}

protocol NetworkServiceProtocol {
    func fetch<T: Decodable>(_ endpoint: String, queryItems: [URLQueryItem]?) async throws -> T
    func post<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T
    func put<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T
    func delete(_ endpoint: String) async throws
}

enum NetworkError: Error, Equatable {
    case invalidURL
    case invalidResponse
    case decodingError(String)
    case encodingError(String)
    case serverError(Int, String?)
    case networkFailure(String)
    case unknown
    
    static func == (lhs: NetworkError, rhs: NetworkError) -> Bool {
        switch (lhs, rhs) {
        case (.invalidURL, .invalidURL), (.invalidResponse, .invalidResponse), (.unknown, .unknown):
            return true
        case let (.decodingError(l), .decodingError(r)), let (.encodingError(l), .encodingError(r)), let (.networkFailure(l), .networkFailure(r)):
            return l == r
        case let (.serverError(l1, l2), .serverError(r1, r2)):
            return l1 == r1 && l2 == r2
        default:
            return false
        }
    }
    
    var localizedDescription: String {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .invalidResponse: return "Invalid response"
        case .decodingError(let msg): return "Decoding error: \(msg)"
        case .encodingError(let msg): return "Encoding error: \(msg)"
        case .serverError(let code, let msg): return "Server error \(code): \(msg ?? "Unknown")"
        case .networkFailure(let msg): return "Network failure: \(msg)"
        case .unknown: return "Unknown error"
        }
    }
}

actor NetworkService: NetworkServiceProtocol {
    static func mock() -> NetworkServiceProtocol {
        return NetworkService()
    }
    
    func fetch<T: Decodable>(_ endpoint: String, queryItems: [URLQueryItem]?) async throws -> T {
        fatalError("Mock only")
    }
    func post<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        fatalError("Mock only")
    }
    func put<T: Decodable, B: Encodable>(_ endpoint: String, body: B) async throws -> T {
        fatalError("Mock only")
    }
    func delete(_ endpoint: String) async throws {
        fatalError("Mock only")
    }
}

/// View states for the items list
enum ItemsViewState: Equatable {
    case idle
    case loading
    case loaded
    case error(String)
    
    static func == (lhs: ItemsViewState, rhs: ItemsViewState) -> Bool {
        switch (lhs, rhs) {
        case (.idle, .idle), (.loading, .loading), (.loaded, .loaded):
            return true
        case let (.error(lhsMsg), .error(rhsMsg)):
            return lhsMsg == rhsMsg
        default:
            return false
        }
    }
}

/// ViewModel for managing items list
@MainActor
class ItemViewModel: ObservableObject {
    
    // MARK: - Published Properties
    
    /// List of items fetched from the backend
    @Published private(set) var items: [Item] = []
    
    /// Current view state
    @Published private(set) var state: ItemsViewState = .idle
    
    /// Error message if any
    @Published private(set) var errorMessage: String?
    
    /// Total count of items (for pagination)
    @Published private(set) var totalCount: Int = 0
    
    /// Search query for filtering items
    @Published var searchQuery: String = ""
    
    /// Selected category filter
    @Published var selectedCategory: String?
    
    // MARK: - Private Properties
    
    /// Network service for API calls
    private let networkService: NetworkServiceProtocol
    
    /// Cancellable for search debounce
    private var searchCancellable: AnyCancellable?
    
    /// Current skip value for pagination
    private var currentSkip: Int = 0
    
    /// Items per page
    private let limit: Int = 20
    
    /// Flag to prevent concurrent fetch requests
    private var isFetching: Bool = false
    
    // MARK: - Computed Properties
    
    /// Filtered items based on search query
    var filteredItems: [Item] {
        if searchQuery.isEmpty {
            return items
        }
        return items.filter { item in
            item.name.localizedCaseInsensitiveContains(searchQuery) ||
            (item.description?.localizedCaseInsensitiveContains(searchQuery) ?? false)
        }
    }
    
    /// Available categories from current items
    var availableCategories: [String] {
        let categories = items.compactMap { $0.category }
        return Array(Set(categories)).sorted()
    }
    
    /// Indicates if there are more items to load
    var canLoadMore: Bool {
        items.count < totalCount && !isFetching
    }
    
    /// Indicates if currently loading
    var isLoading: Bool {
        state == .loading
    }
    
    // MARK: - Initialization
    
    init(networkService: NetworkServiceProtocol = NetworkService()) {
        self.networkService = networkService
        setupSearchDebounce()
    }
    
    // MARK: - Public Methods
    
    /// Fetches items from the backend
    /// - Parameters:
    ///   - skip: Number of items to skip (for pagination)
    ///   - limit: Number of items to fetch
    ///   - reset: Whether to reset the items list
    func fetchItems(skip: Int = 0, limit: Int = 20, reset: Bool = false) async {
        guard !isFetching else { return }
        
        isFetching = true
        
        if reset {
            state = .loading
            items = []
        } else if items.isEmpty {
            state = .loading
        }
        
        defer { isFetching = false }
        
        do {
            var queryItems: [URLQueryItem] = [
                URLQueryItem(name: "skip", value: String(skip)),
                URLQueryItem(name: "limit", value: String(limit))
            ]
            
            if let category = selectedCategory {
                queryItems.append(URLQueryItem(name: "category", value: category))
            }
            
            let response: ItemsResponse = try await networkService.fetch(
                "/items",
                queryItems: queryItems
            )
            
            if reset {
                self.items = response.items
            } else {
                self.items.append(contentsOf: response.items)
            }
            
            self.totalCount = response.total
            self.currentSkip = skip + response.items.count
            self.state = .loaded
            self.errorMessage = nil
            
        } catch let error as NetworkError {
            self.state = .error(error.localizedDescription)
            self.errorMessage = error.localizedDescription
        } catch {
            self.state = .error(error.localizedDescription)
            self.errorMessage = error.localizedDescription
        }
    }
    
    /// Refreshes the items list (resets and fetches from beginning)
    func refresh() async {
        currentSkip = 0
        await fetchItems(skip: 0, limit: limit, reset: true)
    }
    
    /// Loads more items (pagination)
    func loadMore() async {
        guard canLoadMore else { return }
        await fetchItems(skip: currentSkip, limit: limit, reset: false)
    }
    
    /// Creates a new item
    /// - Parameter item: The item to create
    func createItem(name: String, description: String?, category: String?, isActive: Bool = true) async {
        state = .loading
        
        do {
            let request = CreateItemRequest(
                name: name,
                description: description,
                category: category,
                isActive: isActive
            )
            
            let newItem: Item = try await networkService.post("/items", body: request)
            self.items.insert(newItem, at: 0)
            self.totalCount += 1
            self.state = .loaded
            self.errorMessage = nil
            
        } catch let error as NetworkError {
            self.state = .error(error.localizedDescription)
            self.errorMessage = error.localizedDescription
        } catch {
            self.state = .error(error.localizedDescription)
            self.errorMessage = error.localizedDescription
        }
    }
    
    /// Updates an existing item
    /// - Parameters:
    ///   - id: The item ID
    ///   - updates: The fields to update
    func updateItem(id: UUID, name: String? = nil, description: String? = nil, category: String? = nil, isActive: Bool? = nil) async {
        do {
            let request = UpdateItemRequest(
                name: name,
                description: description,
                category: category,
                isActive: isActive
            )
            
            let updatedItem: Item = try await networkService.put("/items/\(id.uuidString)", body: request)
            
            if let index = self.items.firstIndex(where: { $0.id == id }) {
                self.items[index] = updatedItem
            }
            
            self.errorMessage = nil
            
        } catch let error as NetworkError {
            self.errorMessage = error.localizedDescription
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }
    
    /// Deletes an item
    /// - Parameter id: The item ID to delete
    func deleteItem(id: UUID) async {
        do {
            try await networkService.delete("/items/\(id.uuidString)")
            
            self.items.removeAll { $0.id == id }
            self.totalCount -= 1
            self.errorMessage = nil
            
        } catch let error as NetworkError {
            self.errorMessage = error.localizedDescription
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }
    
    /// Clears any error state
    func clearError() {
        errorMessage = nil
        if case .error = state {
            state = items.isEmpty ? .idle : .loaded
        }
    }
    
    // MARK: - Private Methods
    
    /// Sets up debounced search
    private func setupSearchDebounce() {
        searchCancellable = $searchQuery
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .removeDuplicates()
            .sink { [weak self] _ in
                // Search is handled via filteredItems computed property
                // For server-side search, uncomment the following:
                // Task { await self?.refresh() }
            }
    }
}

// MARK: - Preview Support

extension ItemViewModel {
    /// Creates a preview ViewModel with sample data
    static func preview() -> ItemViewModel {
        let viewModel = ItemViewModel(networkService: NetworkService.mock())
        viewModel.items = [
            Item(name: "Sample Item 1", description: "This is a sample item", category: "Category A", isActive: true),
            Item(name: "Sample Item 2", description: "Another sample item", category: "Category B", isActive: true),
            Item(name: "Sample Item 3", description: nil, category: "Category A", isActive: false)
        ]
        viewModel.totalCount = 3
        viewModel.state = ItemsViewState.loaded
        return viewModel
    }
}
