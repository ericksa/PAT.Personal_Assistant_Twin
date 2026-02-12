import SwiftUI

@main
struct PATApp: App {
    var body: some Scene {
        WindowGroup {
            NavigationView {
                List {
                    NavigationLink(destination: UserListView()) {
                        Text("Users")
                            .font(.headline)
                    }
                    
                    NavigationLink(destination: ProductListView()) {
                        Text("Products")
                            .font(.headline)
                    }
                    
                    NavigationLink(destination: CartView()) {
                        Text("Cart")
                            .font(.headline)
                    }
                    
                    NavigationLink(destination: OrderListView()) {
                        Text("Orders")
                            .font(.headline)
                    }
                }
                .navigationTitle("PAT App")
                .navigationBarTitleDisplayMode(.large)
            }
        }
    }
}