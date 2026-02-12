import SwiftUI

struct ProductListView: View {
    @StateObject private var viewModel = ProductViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.products) { product in
                ProductListCell(product: product)
                    .onTapGesture {
                        // Handle tap gesture for navigation to detail view
                        // This would typically navigate to ProductDetailView with the selected product
                    }
            }
            .navigationTitle("Products")
            .onAppear {
                viewModel.fetchProducts()
            }
            .refreshable {
                viewModel.fetchProducts()
            }
        }
        .alert(item: $viewModel.errorMessage) { error in
            Alert(title: Text("Error"), message: Text(error), dismissButton: .default(Text("OK")))
        }
        .overlay(
            Group {
                if viewModel.isLoading {
                    ProgressView()
                        .padding()
                }
            }
        )
    }
}