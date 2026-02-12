import Foundation

protocol RepositoryProtocol {
    associatedtype Model
    
    func getAll(completion: @escaping (Result<[Model], Error>) -> Void)
    func getById(_ id: Int, completion: @escaping (Result<Model, Error>) -> Void)
    func create(_ model: Model, completion: @escaping (Result<Model, Error>) -> Void)
    func update(_ model: Model, completion: @escaping (Result<Model, Error>) -> Void)
    func delete(_ id: Int, completion: @escaping (Result<Bool, Error>) -> Void)
}