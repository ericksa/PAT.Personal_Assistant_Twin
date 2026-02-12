import Foundation

class OrderViewModel: BaseViewModel {
    @Published var orders: [Order] = []
    
    func fetchOrders() {
        isLoading = true
        errorMessage = nil
        
        NetworkManager.shared.request(url: "https://api.yourcompany.com/v1/orders", method: .get) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    self?.orders = response.data
                case .failure(let error):
                    self?.handleError(error)
                }
            }
        }
    }
}