import SwiftUI

struct TabBarView: View {
    var body: some View {
        TabView {
            UserListView()
                .tabItem {
                    Image("UserIcon")
                    Text("Users")
                }
            
            ProductListView()
                .tabItem {
                    Image("ProductIcon")
                    Text("Products")
                }
            
            CartView()
                .tabItem {
                    Image("CartIcon")
                    Text("Cart")
                }
            
            OrderListView()
                .tabItem {
                    Image("OrderIcon")
                    Text("Orders")
                }
        }
        .navigationBarTitleDisplayMode(.inline)
    }
}