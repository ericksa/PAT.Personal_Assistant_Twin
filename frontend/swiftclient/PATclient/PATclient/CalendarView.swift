import SwiftUI

struct CalendarView: View {
    @StateObject var viewModel = CalendarViewModel()
    @State private var showingCreateEvent = false
    
    var body: some View {
        NavigationView {
            List {
                if viewModel.isLoading && viewModel.events.isEmpty {
                    ProgressView("Loading events...")
                } else if viewModel.events.isEmpty {
                    Text("No events found")
                        .foregroundColor(.secondary)
                } else {
                    ForEach(viewModel.events) { event in
                        EventRow(event: event)
                    }
                    .onDelete { indexSet in
                        for index in indexSet {
                            Task {
                                await viewModel.deleteEvent(viewModel.events[index])
                            }
                        }
                    }
                }
            }
            .navigationTitle("Calendar")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showingCreateEvent = true }) {
                        Image(systemName: "plus")
                    }
                }
                ToolbarItem(placement: .navigation) {
                    Button(action: { 
                        Task {
                            await viewModel.fetchEvents()
                        }
                    }) {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .sheet(isPresented: $showingCreateEvent) {
                CreateEventView(viewModel: viewModel)
            }
            .onAppear {
                Task {
                    await viewModel.fetchEvents()
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

struct EventRow: View {
    let event: CalendarEvent
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(event.title)
                    .font(.headline)
                Spacer()
                if let type = event.eventType.capitalized as String? {
                    Text(type)
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.1))
                        .cornerRadius(4)
                }
            }
            
            HStack {
                Image(systemName: "calendar")
                Text(event.startDate)
                if let startTime = event.startTime {
                    Text(startTime)
                }
            }
            .font(.subheadline)
            .foregroundColor(.secondary)
            
            if let location = event.location {
                HStack {
                    Image(systemName: "mappin.and.ellipse")
                    Text(location)
                }
                .font(.subheadline)
                .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}
