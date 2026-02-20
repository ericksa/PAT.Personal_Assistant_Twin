import Foundation
import AVFoundation
import SwiftUI

/// Errors that can occur during voice operations
enum VoiceError: Error, LocalizedError, Equatable {
    case permissionDenied
    case recordingFailed(String)
    case transcriptionFailed(String)
    case invalidAudioData
    case networkError(Error)
    case invalidResponse
    case decodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Microphone access denied. Please enable in System Settings."
        case .recordingFailed(let message):
            return "Recording failed: \(message)"
        case .transcriptionFailed(let message):
            return "Transcription failed: \(message)"
        case .invalidAudioData:
            return "Invalid audio data"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        }
    }
    
    static func == (lhs: VoiceError, rhs: VoiceError) -> Bool {
        switch (lhs, rhs) {
        case (.permissionDenied, .permissionDenied):
            return true
        case (.recordingFailed(let l), .recordingFailed(let r)):
            return l == r
        case (.transcriptionFailed(let l), .transcriptionFailed(let r)):
            return l == r
        case (.invalidAudioData, .invalidAudioData):
            return true
        case (.networkError, .networkError):
            return true // Can't compare Error types directly
        case (.invalidResponse, .invalidResponse):
            return true
        case (.decodingError, .decodingError):
            return true
        default:
            return false
        }
    }
}

/// Response from Whisper transcription service
struct WhisperResponse: Codable {
    let text: String
}

/// Manages voice recording and transcription
@MainActor
class VoiceManager: NSObject, ObservableObject {
    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var transcript = ""
    @Published var lastError: VoiceError?
    
    private var audioRecorder: AVAudioRecorder?
    private var recordingURL: URL?
    private let whisperURL: URL
    private let audioSettings: [String: Any]
    
    /// Initialize VoiceManager with configurable endpoint
    /// - Parameter whisperEndpoint: URL for the Whisper transcription service
    init(whisperEndpoint: String = "http://localhost:8004/transcribe") {
        self.whisperURL = URL(string: whisperEndpoint)!
        self.audioSettings = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false
        ]
        super.init()
    }
    
    /// Toggle recording state
    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            Task {
                await startRecording()
            }
        }
    }
    
    private func startRecording() async {
        let url = getDocumentsDirectory().appendingPathComponent("pat_recording_\(UUID().uuidString).wav")
        self.recordingURL = url
        
        do {
            audioRecorder = try AVAudioRecorder(url: url, settings: audioSettings)
            audioRecorder?.prepareToRecord()
            
            guard audioRecorder?.record() == true else {
                lastError = .recordingFailed("Recorder failed to start")
                return
            }
            
            isRecording = true
            lastError = nil
        } catch {
            lastError = .recordingFailed(error.localizedDescription)
        }
    }
    
    private func stopRecording() {
        audioRecorder?.stop()
        isRecording = false
        
        Task {
            await sendToWhisper()
        }
    }
    
    private func sendToWhisper() async {
        guard let url = recordingURL else {
            lastError = .invalidAudioData
            return
        }
        
        isProcessing = true
        defer { isProcessing = false }
        
        do {
            let audioData = try Data(contentsOf: url)
            
            var request = URLRequest(url: whisperURL)
            request.httpMethod = "POST"
            let boundary = "Boundary-\(UUID().uuidString)"
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            
            var body = Data()
            
            // Add boundary and headers safely
            guard let boundaryPrefix = "--\(boundary)\r\n".data(using: .utf8),
                  let contentDisposition = "Content-Disposition: form-data; name=\"file\"; filename=\"recording.wav\"\r\n".data(using: .utf8),
                  let contentType = "Content-Type: audio/wav\r\n\r\n".data(using: .utf8),
                  let boundarySuffix = "\r\n--\(boundary)--\r\n".data(using: .utf8) else {
                throw VoiceError.transcriptionFailed("Failed to encode multipart data")
            }
            
            body.append(boundaryPrefix)
            body.append(contentDisposition)
            body.append(contentType)
            body.append(audioData)
            body.append(boundarySuffix)
            
            request.httpBody = body
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw VoiceError.invalidResponse
            }
            
            guard (200...299).contains(httpResponse.statusCode) else {
                throw VoiceError.transcriptionFailed("HTTP \(httpResponse.statusCode)")
            }
            
            do {
                let result = try JSONDecoder().decode(WhisperResponse.self, from: data)
                transcript = result.text
                await notifyPAT(text: result.text)
                lastError = nil
            } catch {
                throw VoiceError.decodingError(error)
            }
            
        } catch let error as VoiceError {
            lastError = error
        } catch {
            lastError = .networkError(error)
        }
        
        // Clean up temp file
        try? FileManager.default.removeItem(at: url)
    }
    
    private func notifyPAT(text: String) async {
        // TODO: Send to PAT core API for processing
        print("🎤 Heard: \(text)")
    }
    
    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

// MARK: - Data Extension for safe appending

private extension Data {
    mutating func append(_ string: String, using encoding: String.Encoding = .utf8) {
        if let data = string.data(using: encoding) {
            append(data)
        }
    }
}
