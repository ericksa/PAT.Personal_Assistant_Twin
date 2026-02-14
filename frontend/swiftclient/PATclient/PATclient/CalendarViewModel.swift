import Foundation
import Combine

@MainActor
class CalendarViewModel: ObservableObject {
    @Published var events: [CalendarEvent] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var selectedDate: Date = Date()

    private let service = PATCoreService.shared

    func fetchEvents() async {
        isLoading = true
        errorMessage = nil

        do {
            events = try await service.listEvents()
        } catch {
            errorMessage = "Failed to load events: \(error.localizedDescription)"
        }

        isLoading = false
    }

    func deleteEvent(_ event: CalendarEvent) async {
        guard let id = event.id else { return }

        do {
            try await service.deleteEvent(id: id)
            events.removeAll { $0.id == id }
        } catch {
            errorMessage = "Failed to delete event: \(error.localizedDescription)"
        }
    }

    func addEvent(_ event: CalendarEvent) async {
        do {
            let createdEvent = try await service.createEvent(event)
            events.append(createdEvent)
            // Sort events by date and time
            sortEvents()
        } catch {
            errorMessage = "Failed to add event: \(error.localizedDescription)"
        }
    }

    func updateEvent(_ event: CalendarEvent) async {
        guard let id = event.id else { return }

        do {
            try await service.updateEvent(id: id, event: event.toPartial)
            if let index = events.firstIndex(where: { $0.id == id }) {
                events[index] = event
            }
            sortEvents()
        } catch {
            errorMessage = "Failed to update event: \(error.localizedDescription)"
        }
    }

    func previousDay() {
        selectedDate = Calendar.current.date(byAdding: .day, value: -1, to: selectedDate) ?? selectedDate
    }

    func nextDay() {
        selectedDate = Calendar.current.date(byAdding: .day, value: 1, to: selectedDate) ?? selectedDate
    }

    func today() {
        selectedDate = Date()
    }

    private func sortEvents() {
        events.sort { (e1, e2) -> Bool in
            if e1.startDate != e2.startDate {
                return e1.startDate < e2.startDate
            }
            return (e1.startTime ?? "") < (e2.startTime ?? "")
        }
    }
}
