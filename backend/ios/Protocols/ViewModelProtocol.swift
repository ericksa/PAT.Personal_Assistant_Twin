import Foundation

protocol ViewModelProtocol {
    associatedtype Model
    
    var isLoading: Bool { get set }
    var errorMessage: String? { get set }
    
    func fetchData()
    func handleError(_ error: Error)
}