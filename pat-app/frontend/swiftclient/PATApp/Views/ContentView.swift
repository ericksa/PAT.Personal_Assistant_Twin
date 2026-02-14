//
//  ContentView.swift
//  PATApp
//
//  Created by PAT on 2/13/26.
//

import SwiftUI

/// Main content view displaying a list of items from the backend
struct ContentView: View {
    
    // MARK: - Properties
    
    /// ViewModel managing item data
    @StateObject private var viewModel = ItemViewModel()
    
    /// State for showing create item sheet
    @State private var showCreateSheet = false
    
    /// State for showing item details
    @State private var selectedItem: Item?
    
    // MARK: - Body
    
    var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            detailView
        }
        .navigationTitle("Items")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(action: { showCreateSheet = true }) {
                    Label("Add Item", systemImage: "plus")
                }
            }
            
            ToolbarItem(placement: .automatic) {
                refreshButton
            }
        }
        .sheet(isPresented: $showCreateSheet) {
            CreateItemSheet(viewModel: viewModel)
        }
        .task {
            if viewModel.items.isEmpty {
                await viewModel.fetchItems()
            }
        }
    }
    
    // MARK: - Sidebar View
    
    private var sidebar: some View {
        VStack(spacing: 0) {
            // Search Bar
            searchBar
            
            // Category Filter
            categoryFilter
            
            Divider()
            
            // Items List
            itemsList
        }
    }
    
    // MARK: - Search Bar
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search items...", text: $viewModel.searchQuery)
                .textFieldStyle(PlainTextFieldStyle())
            
            if !viewModel.searchQuery.isEmpty {
                Button(action: { viewModel.searchQuery = "" }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding()
        .background(Color(.textBackgroundColor))
    }
    
    // MARK: - Category Filter
    
    private var categoryFilter: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Categories")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.horizontal)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    CategoryChip(
                        title: "All",
                        isSelected: viewModel.selectedCategory == nil,
                        action: { viewModel.selectedCategory = nil }
                    )
                    
                    ForEach(viewModel.availableCategories, id: \.self) { category in
                        CategoryChip(
                            title: category,
                            isSelected: viewModel.selectedCategory == category,
                            action: { viewModel.selectedCategory = category }
                        )
                    }
                }
                .padding(.horizontal)
            }
        }
        .padding(.vertical, 8)
        .background(Color(.windowBackgroundColor))
    }
    
    // MARK: - Items List
    
    private var itemsList: some View {
        List(selection: $selectedItem) {
            if viewModel.filteredItems.isEmpty {
                Section {
                    emptyState
                }
            } else {
                Section(header: Text("\(viewModel.totalCount) items")) {
                    ForEach(viewModel.filteredItems) { item in
                        ItemRow(item: item)
                            .tag(item)
                    }
                    .onDelete { indexSet in
                        Task {
                            for index in indexSet {
                                let item = viewModel.filteredItems[index]
                                await viewModel.deleteItem(id: item.id)
                            }
                        }
                    }
                    
                    // Load more button
                    if viewModel.canLoadMore {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                            .onAppear {
                                Task { await viewModel.loadMore() }
                            }
                    }
                }
            }
        }
        .listStyle(.sidebar)
    }
    
    // MARK: - Empty State
    
    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "tray")
                .font(.system(size: 48))
                .foregroundColor(.secondary)
            
            if viewModel.isLoading {
                ProgressView("Loading...")
            } else if let errorMessage = viewModel.errorMessage {
                VStack(spacing: 8) {
                    Text("Error loading items")
                        .font(.headline)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    Button("Retry") {
                        Task { await viewModel.refresh() }
                    }
                    .buttonStyle(.borderedProminent)
                }
            } else {
                Text("No items found")
                    .font(.headline)
                    .foregroundColor(.secondary)
                
                Button("Create First Item") {
                    showCreateSheet = true
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
    
    // MARK: - Detail View
    
    @ViewBuilder
    private var detailView: some View {
        if let selectedItem = selectedItem {
            ItemDetailView(item: selectedItem, viewModel: viewModel)
        } else {
            EmptySelectionView()
        }
    }
    
    // MARK: - Refresh Button
    
    private var refreshButton: some View {
        Button(action: {
            Task { await viewModel.refresh() }
        }) {
            if viewModel.isLoading {
                ProgressView()
                    .controlSize(.small)
            } else {
                Label("Refresh", systemImage: "arrow.clockwise")
            }
        }
        .disabled(viewModel.isLoading)
    }
}

// MARK: - Item Row View

struct ItemRow: View {
    let item: Item
    
    var body: some View {
        HStack(spacing: 12) {
            // Status indicator
            Circle()
                .fill(item.isActive ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.headline)
                
                if let category = item.category {
                    Text(category)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            Spacer()
            
            if let description = item.description, !description.isEmpty {
                Image(systemName: "text.quote")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Item Detail View

struct ItemDetailView: View {
    let item: Item
    @ObservedObject var viewModel: ItemViewModel
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(item.name)
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        HStack(spacing: 12) {
                            StatusBadge(isActive: item.isActive)
                            
                            if let category = item.category {
                                CategoryBadge(category: category)
                            }
                        }
                    }
                    
                    Spacer()
                    
                    Menu {
                        Button(role: .destructive) {
                            Task { await viewModel.deleteItem(id: item.id) }
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                            .font(.title2)
                    }
                }
                
                Divider()
                
                // Description
                if let description = item.description, !description.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Description")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        Text(description)
                            .font(.body)
                    }
                }
                
                // Metadata
                VStack(alignment: .leading, spacing: 12) {
                    Text("Details")
                        .font(.headline)
                        .foregroundColor(.secondary)
                    
                    DetailRow(label: "ID", value: item.id.uuidString)
                    DetailRow(label: "Created", value: formatDate(item.createdAt))
                    DetailRow(label: "Status", value: item.isActive ? "Active" : "Inactive")
                    if let category = item.category {
                        DetailRow(label: "Category", value: category)
                    }
                }
                
                Spacer()
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(Color(.windowBackgroundColor))
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
}

// MARK: - Empty Selection View

struct EmptySelectionView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 64))
                .foregroundColor(.secondary)
            
            Text("Select an Item")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Choose an item from the list to view its details")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.windowBackgroundColor))
    }
}

// MARK: - Supporting Views

struct CategoryChip: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .fontWeight(isSelected ? .semibold : .regular)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? Color.accentColor : Color.secondary.opacity(0.1))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(16)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct StatusBadge: View {
    let isActive: Bool
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(isActive ? Color.green : Color.red)
                .frame(width: 6, height: 6)
            
            Text(isActive ? "Active" : "Inactive")
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(isActive ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
        .cornerRadius(8)
    }
}

struct CategoryBadge: View {
    let category: String
    
    var body: some View {
        Text(category)
            .font(.caption)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.blue.opacity(0.1))
            .foregroundColor(.blue)
            .cornerRadius(8)
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 80, alignment: .leading)
            
            Text(value)
                .font(.body)
                .textSelection(.enabled)
            
            Spacer()
        }
    }
}

// MARK: - Create Item Sheet

struct CreateItemSheet: View {
    @ObservedObject var viewModel: ItemViewModel
    @Environment(\.dismiss) var dismiss
    
    @State private var name = ""
    @State private var description = ""
    @State private var category = ""
    @State private var isActive = true
    
    var body: some View {
        NavigationStack {
            Form {
                Section("Item Information") {
                    TextField("Name", text: $name)
                    
                    TextField("Category", text: $category)
                    
                    Toggle("Active", isOn: $isActive)
                }
                
                Section("Description") {
                    TextEditor(text: $description)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle("New Item")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await viewModel.createItem(
                                name: name,
                                description: description.isEmpty ? nil : description,
                                category: category.isEmpty ? nil : category,
                                isActive: isActive
                            )
                            dismiss()
                        }
                    }
                    .disabled(name.isEmpty || viewModel.isLoading)
                }
            }
        }
        .frame(minWidth: 400, minHeight: 400)
    }
}

// MARK: - Preview

#Preview("Content View") {
    ContentView()
}

#Preview("Item Detail") {
    struct PreviewContainer: View {
        let item = Item(
            id: UUID(),
            name: "Sample Item",
            description: "This is a detailed description of the sample item that shows how the detail view renders longer text content.",
            category: "Sample Category",
            isActive: true,
            createdAt: Date()
        )
        
        var body: some View {
            ItemDetailView(item: item, viewModel: ItemViewModel())
        }
    }
    
    return PreviewContainer()
}

#Preview("Empty State") {
    EmptySelectionView()
}

// Forward declaration for Item
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

// Forward declaration for ItemViewModel
@MainActor
class ItemViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var state = ItemsViewState.idle
    @Published var errorMessage: String?
    @Published var totalCount = 0
    @Published var searchQuery = ""
    @Published var selectedCategory: String?
    
    var filteredItems: [Item] {
        if searchQuery.isEmpty { return items }
        return items.filter { $0.name.localizedCaseInsensitiveContains(searchQuery) }
    }
    
    var availableCategories: [String] {
        Array(Set(items.compactMap { $0.category })).sorted()
    }
    
    var canLoadMore: Bool { false }
    var isLoading: Bool { state == .loading }
    
    init() {}
    
    func fetchItems() async {}
    func refresh() async {}
    func loadMore() async {}
    func createItem(name: String, description: String?, category: String?, isActive: Bool) async {}
    func deleteItem(id: UUID) async {}
}

enum ItemsViewState {
    case idle, loading, loaded, error(String)
}
