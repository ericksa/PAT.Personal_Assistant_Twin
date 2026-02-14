import SwiftUI

struct CalendarView: View {
    @StateObject var viewModel = CalendarViewModel()
    @State private var showingCreateEvent = false
    @State private var selectedEvent: CalendarEvent?

    var body: some View {
        NavigationSplitView {
            // Sidebar with upcoming events
            VStack(spacing: 0) {
                Text("Calendar")
                    .font(.headline)
                    .fontWeight(.semibold)
                    .padding()

                Divider()

                List(selection: $selectedEvent) {
                    Section("Today") {
                        ForEach(viewModel.events.filter { isToday($0.startDate) }) { event in
                            EventSidebarRow(event: event)
                                .tag(event)
                        }
                    }

                    Section("Upcoming") {
                        ForEach(viewModel.events.filter { !isToday($0.startDate) }) { event in
                            EventSidebarRow(event: event)
                                .tag(event)
                        }
                    }
                }
                .listStyle(.sidebar)

                // Quick stats at bottom
                VStack(spacing: 8) {
                    Divider()
                    HStack {
                        StatBadge(count: viewModel.events.count, label: "Events", icon: "calendar")
                        Spacer()
                        StatBadge(count: viewModel.events.filter { isToday($0.startDate) }.count, label: "Today", icon: "sun.max")
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                }
            }
            .nativeSidebar()
            .navigationSplitViewColumnWidth(min: 220, ideal: 260)
        } detail: {
            // Main content area
            VStack(spacing: 0) {
                // Toolbar
                HStack {
                    Text(viewModel.selectedDate, style: .date)
                        .font(.headline)

                    Spacer()

                    HStack(spacing: 8) {
                        Button(action: { viewModel.previousDay() }) {
                            Image(systemName: "chevron.left")
                        }
                        .buttonStyle(.borderless)

                        Button(action: { viewModel.today() }) {
                            Text("Today")
                        }
                        .buttonStyle(.bordered)
                        .controlSize(.small)

                        Button(action: { viewModel.nextDay() }) {
                            Image(systemName: "chevron.right")
                        }
                        .buttonStyle(.borderless)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(.ultraThinMaterial)

                Divider()

                // Events list
                ScrollView {
                    LazyVStack(spacing: 0) {
                        if viewModel.isLoading && viewModel.events.isEmpty {
                            LoadingView(message: "Loading events...")
                        } else if viewModel.events.isEmpty {
                            EmptyStateView(
                                icon: "calendar.badge.exclamationmark",
                                title: "No Events",
                                message: "Your calendar is empty"
                            )
                        } else {
                            ForEach(viewModel.events) { event in
                                ModernEventRow(event: event, onDelete: {
                                    Task { await viewModel.deleteEvent(event) }
                                }, onEdit: {
                                    selectedEvent = event
                                    showingCreateEvent = true
                                })
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)

                                if event.id != viewModel.events.last?.id {
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
            .navigationTitle("Calendar")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: {
                        selectedEvent = nil
                        showingCreateEvent = true
                    }) {
                        Image(systemName: "plus")
                    }
                    .help("Add Event")
                }

                ToolbarItem(placement: .navigation) {
                    Button(action: {
                        Task { await viewModel.fetchEvents() }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                    .help("Refresh")
                }
            }
        }
        .sheet(isPresented: $showingCreateEvent) {
            CreateEventView(viewModel: viewModel, existingEvent: selectedEvent)
                .frame(minWidth: 500, minHeight: 400)
        }
        .task {
            await viewModel.fetchEvents()
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

    private func isToday(_ dateString: String) -> Bool {
        // Simple check - in production, parse the date properly
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        let today = formatter.string(from: Date())
        return dateString.contains(today)
    }
}

// MARK: - Event Sidebar Row
struct EventSidebarRow: View {
    let event: CalendarEvent

    var body: some View {
        HStack(spacing: 10) {
            // Event type indicator
            Circle()
                .fill(eventColor)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(event.title)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .lineLimit(1)

                HStack(spacing: 4) {
                    Image(systemName: "clock")
                        .font(.caption2)
                    Text(event.startTime ?? "All day")
                        .font(.caption)
                }
                .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(.vertical, 4)
    }

    private var eventColor: Color {
        switch event.eventType.lowercased() {
        case "meeting": return .blue
        case "appointment": return .green
        case "reminder": return .orange
        case "task": return .purple
        default: return .gray
        }
    }
}

// MARK: - Modern Event Row
struct ModernEventRow: View {
    let event: CalendarEvent
    let onDelete: () -> Void
    let onEdit: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            // Time column
            VStack(alignment: .trailing, spacing: 2) {
                Text(event.startTime ?? "All day")
                    .font(.subheadline)
                    .fontWeight(.semibold)

                if let endTime = event.endTime {
                    Text(endTime)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .frame(width: 60, alignment: .trailing)

            // Event indicator
            Rectangle()
                .fill(eventColor)
                .frame(width: 4)
                .cornerRadius(2)

            // Event details
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(event.title)
                        .font(.subheadline)
                        .fontWeight(.semibold)

                    Spacer()

                    EventTypeBadge(type: event.eventType)
                }

                if let description = event.description, !description.isEmpty {
                    Text(description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }

                if let location = event.location, !location.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "mappin.and.ellipse")
                            .font(.caption)
                        Text(location)
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                }

                Spacer()

                Menu {
                    Button(action: onEdit) {
                        Label("Edit", systemImage: "pencil")
                    }

                    Button(action: onDelete) {
                        Label("Delete", systemImage: "trash")
                    }
                    .foregroundColor(.red)
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.secondary)
                }
                .menuStyle(.borderlessButton)
            }

            Spacer()
        }
        .padding(.vertical, 4)
    }

    private var eventColor: Color {
        switch event.eventType.lowercased() {
        case "meeting": return .blue
        case "appointment": return .green
        case "reminder": return .orange
        case "task": return .purple
        default: return .gray
        }
    }
}

// MARK: - Event Type Badge
struct EventTypeBadge: View {
    let type: String

    var body: some View {
        Text(type.capitalized)
            .font(.caption2)
            .fontWeight(.medium)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(typeColor.opacity(0.1))
            .foregroundColor(typeColor)
            .cornerRadius(4)
    }

    private var typeColor: Color {
        switch type.lowercased() {
        case "meeting": return .blue
        case "appointment": return .green
        case "reminder": return .orange
        case "task": return .purple
        default: return .gray
        }
    }
}

// MARK: - Priority Indicator
struct PriorityIndicator: View {
    let priority: Int

    var body: some View {
        HStack(spacing: 2) {
            ForEach(0..<min(priority, 3), id: \.self) { _ in
                Image(systemName: "exclamationmark")
                    .font(.caption2)
                    .foregroundColor(priorityColor)
            }
        }
    }

    private var priorityColor: Color {
        if priority >= 3 { return .red }
        if priority == 2 { return .orange }
        return .yellow
    }
}

// MARK: - Stat Badge
struct StatBadge: View {
    let count: Int
    let label: String
    let icon: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption)
            Text("\(count)")
                .font(.caption)
                .fontWeight(.semibold)
            Text(label)
                .font(.caption)
        }
        .foregroundColor(.secondary)
    }
}

// MARK: - Loading View
struct LoadingView: View {
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Spacer()
            ProgressView()
                .controlSize(.regular)
            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Empty State View
struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundColor(.secondary.opacity(0.5))

            VStack(spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(message)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    CalendarView()
}
