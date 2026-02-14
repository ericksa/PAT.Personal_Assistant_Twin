import SwiftUI

struct CreateEventView: View {
    @ObservedObject var viewModel: CalendarViewModel
    @Environment(\.dismiss) var dismiss

    let existingEvent: CalendarEvent?

    @State private var title = ""
    @State private var description = ""
    @State private var startDate = Date()
    @State private var startTime = Date()
    @State private var endDate = Date()
    @State private var endTime = Date()
    @State private var location = ""
    @State private var eventType = "meeting"

    let eventTypes = ["meeting", "call", "task", "personal", "other"]

    init(viewModel: CalendarViewModel, existingEvent: CalendarEvent? = nil) {
        self.viewModel = viewModel
        self.existingEvent = existingEvent
    }

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Event Details")) {
                    TextField("Title", text: $title)
                    TextField("Description", text: $description)
                    TextField("Location", text: $location)
                    Picker("Event Type", selection: $eventType) {
                        ForEach(eventTypes, id: \.self) { type in
                            Text(type.capitalized).tag(type)
                        }
                    }
                }

                Section(header: Text("Date & Time")) {
                    DatePicker("Start Date", selection: $startDate, displayedComponents: .date)
                    DatePicker("Start Time", selection: $startTime, displayedComponents: .hourAndMinute)
                    DatePicker("End Date", selection: $endDate, displayedComponents: .date)
                    DatePicker("End Time", selection: $endTime, displayedComponents: .hourAndMinute)
                }
            }
            .navigationTitle(existingEvent != nil ? "Edit Event" : "New Event")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveEvent()
                    }
                    .disabled(title.isEmpty)
                }
            }
            .onAppear {
                if let event = existingEvent {
                    // Populate fields with existing event data
                    title = event.title
                    description = event.description ?? ""
                    location = event.location ?? ""
                    eventType = event.eventType

                    let dateFormatter = DateFormatter()
                    dateFormatter.dateFormat = "yyyy-MM-dd"

                    let timeFormatter = DateFormatter()
                    timeFormatter.dateFormat = "HH:mm"

                    if let sDate = dateFormatter.date(from: event.startDate) {
                        startDate = sDate
                    }
                    if let eDate = dateFormatter.date(from: event.endDate) {
                        endDate = eDate
                    }
                    if let sTime = event.startTime, let time = timeFormatter.date(from: sTime) {
                        startTime = time
                    }
                    if let eTime = event.endTime, let time = timeFormatter.date(from: eTime) {
                        endTime = time
                    }
                }
            }
        }
    }

    private func saveEvent() {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"

        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm"

        let event = CalendarEvent(
            id: existingEvent?.id, // Keep existing ID if editing
            title: title,
            description: description.isEmpty ? nil : description,
            startDate: dateFormatter.string(from: startDate),
            startTime: timeFormatter.string(from: startTime),
            endDate: dateFormatter.string(from: endDate),
            endTime: timeFormatter.string(from: endTime),
            location: location.isEmpty ? nil : location,
            eventType: eventType,
            priority: existingEvent?.priority
        )

        Task {
            if existingEvent != nil {
                await viewModel.updateEvent(event)
            } else {
                await viewModel.addEvent(event)
            }
            dismiss()
        }
    }
}
