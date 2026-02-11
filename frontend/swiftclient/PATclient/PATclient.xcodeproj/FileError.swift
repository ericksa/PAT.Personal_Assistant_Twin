enum FileError: Error, LocalizedError {
    case userCancelled
    case fileReadError
    case fileWriteError
    case invalidFileFormat
    
    var errorDescription: String? {
        switch self {
        case .userCancelled:
            return "Operation cancelled by user"
        case .fileReadError:
            return "Failed to read file"
        case .fileWriteError:
            return "Failed to write file"
        case .invalidFileFormat:
            return "Invalid file format"
        }
    }
}
