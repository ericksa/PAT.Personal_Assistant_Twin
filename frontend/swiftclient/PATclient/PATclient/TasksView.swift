import SwiftUI

struct TasksView: View {
    @StateObject var viewModel = TasksViewModel()
    @State private var showingCreateTask = false
    @State private var selectedStatus: TaskStatus = .pending
    @State private var selectedTask: PATTask?
    @State private var showCompleted: Bool = false

    var body: some View {
        NavigationSplitView {
            // Sidebar with task filters
            VStack(spacing: 0) {
                Text("Tasks")
                    .font(.headline)
                    .fontWeight(.semibold)
                    .padding()

                Divider()

                // Status filter
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(TaskStatus.allCases.enumerated()), id: \.offset) { index, status in
                        StatusFilterRow(
                            status: status,
                            count: taskCount(for: status),
                            isSelected: selectedStatus == status
                        ) {
                            selectedStatus = status
                            Task { await viewModel.fetchTasks(status: status) }
                        }
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Divider()

                // Quick actions
                VStack(alignment: .leading, spacing: 8) {
                    Button(action: { Task { await viewModel.suggestPriorities() } }) {
                        Label("AI Suggestions", systemImage: "sparkles")
                            .font(.subheadline)
                    }
                    .buttonStyle(.borderless)

                    Button(action: { Task { await viewModel.syncTasks() } }) {
                        Label("Sync", systemImage: "arrow.clockwise")
                            .font(.subheadline)
                    }
                    .buttonStyle(.borderless)

                    Button(action: { Task { await viewModel.getFocusTasks() } }) {
                        Label("Focus Tasks", systemImage: "target")
                            .font(.subheadline)
                    }
                    .buttonStyle(.borderless)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)

                Spacer()

                // Stats
                VStack(spacing: 8) {
                    Divider()
                    TaskStatsRow(viewModel: viewModel)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                }
            }
            .nativeSidebar()
            .navigationSplitViewColumnWidth(min: 200, ideal: 240)
        } detail: {
            // Main content
            VStack(spacing: 0) {
                // Toolbar
                HStack {
                    Text("\(selectedStatus.rawValue.capitalized) Tasks")
                        .font(.headline)

                    Spacer()

                    if viewModel.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    }

                    Toggle("Show Completed", isOn: $showCompleted)
                        .toggleStyle(.checkbox)
                        .controlSize(.small)

                    Button(action: {
                        selectedTask = nil
                        showingCreateTask = true
                    }) {
                        Label("Add Task", systemImage: "plus")
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(.ultraThinMaterial)

                Divider()

                // Tasks list
                ScrollView {
                    LazyVStack(spacing: 0) {
                        if viewModel.isLoading && viewModel.tasks.isEmpty {
                            LoadingView(message: "Loading tasks...")
                        } else if viewModel.tasks.isEmpty {
                            EmptyStateView(
                                icon: "checklist",
                                title: "No Tasks",
                                message: "You're all caught up!"
                            )
                        } else {
                            ForEach(viewModel.tasks) { task in
                                ModernTaskRow(
                                    task: task,
                                    onComplete: {
                                        Task { await viewModel.completeTask(task) }
                                    },
                                    onEdit: {
                                        selectedTask = task
                                        showingCreateTask = true
                                    },
                                    onDelete: {
                                        Task { await viewModel.deleteTask(task) }
                                    }
                                )
                                .padding(.horizontal, 16)
                                .padding(.vertical, 10)

                                if task.id != viewModel.tasks.last?.id {
                                    Divider()
                                        .padding(.horizontal, 16)
                                }
                            }
                        }
                    }
                    .padding(.vertical, 8)
                }
            }
            .background(Color(nsColor: .windowBackgroundColor))
            .navigationTitle("Tasks")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: {
                        selectedTask = nil
                        showingCreateTask = true
                    }) {
                        Image(systemName: "plus")
                    }
                    .help("Add Task")
                }

                ToolbarItem(placement: .navigation) {
                    Button(action: {
                        Task { await viewModel.syncTasks() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .help("Sync Tasks")
                }
            }
        }
        .sheet(isPresented: $showingCreateTask) {
            CreateTaskView(viewModel: viewModel, existingTask: selectedTask)
                .frame(minWidth: 450, minHeight: 350)
        }
        .task {
            await viewModel.fetchTasks(status: selectedStatus)
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

    private func taskCount(for status: TaskStatus) -> Int {
        // In production, this should query the actual count
        return 0
    }
}

// MARK: - Status Filter Row
struct StatusFilterRow: View {
    let status: TaskStatus
    let count: Int
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: statusIcon)
                    .font(.system(size: 14))
                    .foregroundColor(statusColor)
                    .frame(width: 20)

                Text(status.rawValue.capitalized)
                    .font(.subheadline)
                    .foregroundColor(isSelected ? .primary : .secondary)

                Spacer()

                if count > 0 {
                    Text("\(count)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.1))
                        .cornerRadius(8)
                }

                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.caption)
                        .foregroundColor(.accentColor)
                }
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
            .cornerRadius(6)
        }
        .buttonStyle(.plain)
    }

    private var statusIcon: String {
        switch status {
        case .pending: return "circle"
        case .in_progress: return "arrow.clockwise"
        case .completed: return "checkmark.circle.fill"
        }
    }

    private var statusColor: Color {
        switch status {
        case .pending: return .orange
        case .in_progress: return .blue
        case .completed: return .green
        }
    }
}

// MARK: - Modern Task Row
struct ModernTaskRow: View {
    let task: PATTask
    let onComplete: () -> Void
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Completion button
            Button(action: onComplete) {
                Image(systemName: task.status == .completed ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundColor(task.status == .completed ? .green : .secondary)
            }
            .buttonStyle(.plain)
            .help(task.status == .completed ? "Mark incomplete" : "Mark complete")

            // Priority indicator
            PriorityIndicator(priority: task.priority)
                .frame(width: 4)

            // Task content
            VStack(alignment: .leading, spacing: 4) {
                Text(task.title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .strikethrough(task.status == .completed)
                    .foregroundColor(task.status == .completed ? .secondary : .primary)

                if let description = task.description, !description.isEmpty {
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }

                HStack(spacing: 12) {
                    if let dueDate = task.dueDate {
                        HStack(spacing: 4) {
                            Image(systemName: "calendar")
                                .font(.caption2)
                            Text(dueDate)
                                .font(.caption)
                        }
                        .foregroundColor(isOverdue ? .red : .secondary)
                    }

                    if let tags = task.tags, !tags.isEmpty {
                        HStack(spacing: 4) {
                            ForEach(Array(tags.prefix(2).enumerated()), id: \.offset) { index, tag in
                                TagBadge(text: tag)
                            }
                        }
                    }
                }
            }

            Spacer()

            // Actions menu
            Menu {
                Button(action: onEdit) {
                    Label("Edit", systemImage: "pencil")
                }

                Button(action: onComplete) {
                    Label(
                        task.status == .completed ? "Mark Incomplete" : "Mark Complete",
                        systemImage: task.status == .completed ? "circle" : "checkmark.circle"
                    )
                }

                Divider()

                Button(role: .destructive, action: onDelete) {
                    Label("Delete", systemImage: "trash")
                }
            } label: {
                Image(systemName: "ellipsis.circle")
                    .foregroundColor(.secondary)
            }
            .menuStyle(.borderlessButton)
        }
        .padding(.vertical, 2)
    }

    private var isOverdue: Bool {
        // Simple check - in production, parse date properly
        return false
    }
}

// MARK: - Tag Badge
struct TagBadge: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.caption2)
            .fontWeight(.medium)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Color.accentColor.opacity(0.1))
            .foregroundColor(.accentColor)
            .cornerRadius(4)
    }
}

// MARK: - Task Stats Row
struct TaskStatsRow: View {
    let viewModel: TasksViewModel

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Text("Task Overview")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.secondary)
                Spacer()
            }

            HStack(spacing: 16) {
                StatItem(
                    value: viewModel.tasks.filter { $0.status == .pending }.count,
                    label: "Pending",
                    color: .orange
                )
                StatItem(
                    value: viewModel.tasks.filter { $0.status == .in_progress }.count,
                    label: "In Progress",
                    color: .blue
                )
                StatItem(
                    value: viewModel.tasks.filter { $0.status == .completed }.count,
                    label: "Done",
                    color: .green
                )
            }
        }
    }
}

struct StatItem: View {
    let value: Int
    let label: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 6, height: 6)
            Text("\(value)")
                .font(.caption)
                .fontWeight(.semibold)
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

#Preview {
    TasksView()
}
