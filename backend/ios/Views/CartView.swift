import SwiftUI

struct CartView: View {
    @StateObject private var viewModel = CartViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.cartItems) { item in
                CartListCell(cartItem: item)
                    .onTapGesture {
                        // Handle tap gesture for navigation to detail view
                        // This would typically navigate to CartDetailView with the selected cart item
                    }
            }
            .navigationTitle("Cart")
            .onAppear {
                viewModel.fetchCart()
            }
            .refreshable {
                viewModel.fetchCart()
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