import SwiftUI

struct EmailComposeView: View {
    @Environment(\.dismiss) var dismiss
    @ObservedObject var viewModel: EmailsViewModel
    
    @State private var recipient = ""
    @State private var subject = ""
    @State private var bodyText = ""
    @State private var isSending = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Recipients")) {
                    TextField("To:", text: $recipient)
                }
                
                Section(header: Text("Content")) {
                    TextField("Subject", text: $subject)
                    TextEditor(text: $bodyText)
                        .frame(minHeight: 200)
                }
            }
            .navigationTitle("New Message")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Send") {
                        sendEmail()
                    }
                    .disabled(recipient.isEmpty || subject.isEmpty || isSending)
                }
            }
        }
    }
    
    private func sendEmail() {
        isSending = true
        Task {
            do {
                try await PATCoreService.shared.sendEmail(
                    recipient: recipient,
                    subject: subject,
                    body: bodyText
                )
                dismiss()
            } catch {
                viewModel.errorMessage = "Failed to send: \(error.localizedDescription)"
            }
            isSending = false
        }
    }
}
