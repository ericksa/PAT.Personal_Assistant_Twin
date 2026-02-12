import Foundation

class UserViewModel: BaseViewModel {
    @Published var users: [User] = []
    
    func fetchUsers() {
        isLoading = true
        errorMessage = nil
        
        NetworkManager.shared.request(url: "https://api.yourcompany.com/v1/users", method: .get) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    self?.users = response.data
                case .failure(let error):
                    self?.handleError(error)
                }
            }
        }
    }
}