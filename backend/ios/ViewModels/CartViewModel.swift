import Foundation

class CartViewModel: BaseViewModel {
    @Published var cartItems: [CartItem] = []
    
    func fetchCart() {
        isLoading = true
        errorMessage = nil
        
        NetworkManager.shared.request(url: "https://api.yourcompany.com/v1/cart", method: .get) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    self?.cartItems = response.data
                case .failure(let error):
                    self?.handleError(error)
                }
            }
        }
    }
}