import Foundation

extension String {
    func sanitizedFilename() -> String {
        let invalidCharacters = CharacterSet(charactersIn: ":/\\?*|\"< >")
        return components(separatedBy: invalidCharacters).joined(separator: "_")
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: " ", with: "_")
    }
}