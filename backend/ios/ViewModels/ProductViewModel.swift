import Foundation

class ProductViewModel: BaseViewModel {
    @Published var products: [Product] = []
    
    func fetchProducts() {
        isLoading = true
        errorMessage = nil
        
        NetworkManager.shared.request(url: "https://api.yourcompany.com/v1/products", method: .get) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    self?.products = response.data
                case .failure(let error):
                    self?.handleError(error)
                }
            }
        }
    }
}