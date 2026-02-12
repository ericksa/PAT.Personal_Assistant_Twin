import SwiftUI

struct TasksView: View {
    @StateObject var viewModel = TasksViewModel()
    @State private var showingCreateTask = false
    @State private var selectedStatus: TaskStatus = .pending
    
    var body: some View {
        NavigationView {
            VStack {
                Picker("Status", selection: $selectedStatus) {
                    ForEach(TaskStatus.allCases, id: \.self) { status in
                        Text(status.rawValue.capitalized).tag(status)
                    }
                }
                .pickerStyle(SegmentedPickerStyle())
                .padding()
                .onChange(of: selectedStatus) { newValue in
                    Task {
                        await viewModel.fetchTasks(status: newValue)
                    }
                }
                
                List {
                    if viewModel.isLoading && viewModel.tasks.isEmpty {
                        ProgressView("Loading tasks...")
                    } else if viewModel.tasks.isEmpty {
                        Text("No tasks found")
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(viewModel.tasks) { task in
                            TaskRow(task: task, onComplete: {
                                Task {
                                    await viewModel.completeTask(task)
                                }
                            })
                        }
                    }
                }
            }
            .navigationTitle("Tasks")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingCreateTask = true }) {
                        Image(systemName: "plus")
                    }
                }
                ToolbarItem(placement: .navigation) {
                    Button(action: { 
                        Task {
                            await viewModel.fetchTasks(status: selectedStatus)
                        }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .sheet(isPresented: $showingCreateTask) {
                CreateTaskView(viewModel: viewModel)
            }
            .onAppear {
                Task {
                    await viewModel.fetchTasks(status: selectedStatus)
                }
            }
            .alert("Error", isPresented: Binding<Bool>(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )) {
                Button("OK", role: .cancel) { }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }
}

struct TaskRow: View {
    let task: PATTask
    let onComplete: () -> Void
    
    var body: some View {
        HStack {
            Button(action: onComplete) {
                Image(systemName: task.status == .completed ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(task.status == .completed ? .green : .secondary)
                    .font(.title3)
            }
            .buttonStyle(PlainButtonStyle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(task.title)
                    .font(.headline)
                    .strikethrough(task.status == .completed)
                
                if let description = task.description {
                    Text(description)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            
            Spacer()
            
            PriorityBadge(priority: task.priority)
        }
        .padding(.vertical, 4)
    }
}

struct PriorityBadge: View {
    let priority: TaskPriority
    
    var color: Color {
        switch priority {
        case .urgent: return .red
        case .high: return .orange
        case .medium: return .blue
        case .low: return .gray
        }
    }
    
    var body: some View {
        Text(priority.rawValue.uppercased())
            .font(.caption2)
            .fontWeight(.bold)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color.opacity(0.1))
            .foregroundColor(color)
            .cornerRadius(4)
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(color.opacity(0.3), lineWidth: 1)
            )
    }
}
