import SwiftUI

struct DocumentManagementView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var resumes: [Document] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView("Loading documents…")
                } else if let error = errorMessage {
                    Text(error)
                        .foregroundColor(.red)
                } else if resumes.isEmpty {
                    Text("No documents uploaded.")
                        .foregroundColor(.secondary)
                } else {
                    List(resumes, id: \ .id) { doc in
                        Text(doc.filename)
                    }
                }
            }
            .navigationTitle("Documents")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task { await loadResumes() }
        }
    }
    
    private func loadResumes() async {
        isLoading = true
        errorMessage = nil
        do {
            let fetched = try await IngestService.shared.listResumes()
            await MainActor.run { self.resumes = fetched }
        } catch {
            await MainActor.run { self.errorMessage = "Failed to load documents: \(error.localizedDescription)" }
        }
        isLoading = false
    }
}

#Preview {
    DocumentManagementView()
}
