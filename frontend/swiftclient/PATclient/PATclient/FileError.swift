import Foundation

enum FileError: Error, LocalizedError {
    case userCancelled
    case fileReadError
    case fileWriteError
    
    var errorDescription: String? {
        switch self {
        case .userCancelled:
            return "User cancelled the operation"
        case .fileReadError:
            return "Failed to read file"
        case .fileWriteError:
            return "Failed to write file"
        }
    }
}