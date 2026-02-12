import SwiftUI

struct UserListView: View {
    @StateObject private var viewModel = UserViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.users) { user in
                UserListCell(user: user)
                    .onTapGesture {
                        // Handle tap gesture for navigation to detail view
                        // This would typically navigate to UserDetailView with the selected user
                    }
            }
            .navigationTitle("Users")
            .onAppear {
                viewModel.fetchUsers()
            }
            .refreshable {
                viewModel.fetchUsers()
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