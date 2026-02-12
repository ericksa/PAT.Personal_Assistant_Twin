import SwiftUI

struct CreateTaskView: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var viewModel: TasksViewModel
    
    var body: some View {
        Text("Task Creation Form")
            .padding()
        Button("Close") { dismiss() }
    }
}
