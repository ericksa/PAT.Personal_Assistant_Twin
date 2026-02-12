import Foundation

class BaseViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func handleError(_ error: Error) {
        isLoading = false
        errorMessage = error.localizedDescription
    }
}