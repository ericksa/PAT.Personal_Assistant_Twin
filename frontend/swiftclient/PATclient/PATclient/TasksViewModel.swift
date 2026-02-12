import Foundation
import Combine

@MainActor
class TasksViewModel: ObservableObject {
    @Published var tasks: [PATTask] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let service = PATCoreService.shared
    
    func fetchTasks(status: TaskStatus? = .pending) async {
        isLoading = true
        errorMessage = nil
        
        do {
            tasks = try await service.listTasks(status: status)
        } catch {
            errorMessage = "Failed to load tasks: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func completeTask(_ task: PATTask) async {
        guard let id = task.id else { return }
        
        do {
            try await service.completeTask(id: id)
            tasks.removeAll { $0.id == id }
        } catch {
            errorMessage = "Failed to complete task: \(error.localizedDescription)"
        }
    }
    
    func addTask(_ task: PATTask) async {
        do {
            let createdTask = try await service.createTask(task)
            tasks.append(createdTask)
            sortTasks()
        } catch {
            errorMessage = "Failed to add task: \(error.localizedDescription)"
        }
    }
    
    private func sortTasks() {
        tasks.sort { (t1, t2) -> Bool in
            // Sort by priority (urgent > high > medium > low)
            let priorityOrder: [TaskPriority: Int] = [.urgent: 0, .high: 1, .medium: 2, .low: 3]
            let p1 = priorityOrder[t1.priority] ?? 4
            let p2 = priorityOrder[t2.priority] ?? 4
            
            if p1 != p2 {
                return p1 < p2
            }
            
            return t1.title < t2.title
        }
    }
}
