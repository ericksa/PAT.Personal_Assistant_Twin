import SwiftUI

struct OrderListView: View {
    @StateObject private var viewModel = OrderViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.orders) { order in
                OrderListCell(order: order)
                    .onTapGesture {
                        // Handle tap gesture for navigation to detail view
                        // This would typically navigate to OrderDetailView with the selected order
                    }
            }
            .navigationTitle("Orders")
            .onAppear {
                viewModel.fetchOrders()
            }
            .refreshable {
                viewModel.fetchOrders()
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