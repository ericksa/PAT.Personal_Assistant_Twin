import Foundation

@MainActor
class TasksViewModel: ObservableObject {
    @Published var tasks: [PATTask] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func fetchTasks(status: TaskStatus) async {
        isLoading = true
        do {
            tasks = try await PATCoreService.shared.listTasks(status: status)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
    
    func syncTasks() async {
        _ = try? await PATCoreService.shared.syncTasks()
        await fetchTasks(status: .pending)
    }
    
    func completeTask(_ task: PATTask) async {
        guard let id = task.id else { return }
        try? await PATCoreService.shared.completeTask(id: id)
        await fetchTasks(status: .pending)
    }
    
    func suggestPriorities() async {
        _ = try? await PATCoreService.shared.suggestTaskPriorities()
    }
}
