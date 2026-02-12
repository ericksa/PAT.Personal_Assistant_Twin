import Foundation
import AVFoundation

class VoiceManager: NSObject, ObservableObject {
    @Published var isRecording = false
    @Published var isProcessing = false
    @Published var transcript = ""
    
    private var audioRecorder: AVAudioRecorder?
    private let whisperURL = URL(string: "http://localhost:8004/transcribe")!
    
    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }
    
    private func startRecording() {
        // macOS doesn't use AVAudioSession like iOS
        let url = getDocumentsDirectory().appendingPathComponent("recording.wav")
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: url, settings: settings)
            audioRecorder?.prepareToRecord()
            audioRecorder?.record()
            isRecording = true
        } catch {
            print("Failed to start recording: \(error)")
        }
    }
    
    private func stopRecording() {
        audioRecorder?.stop()
        isRecording = false
        sendToWhisper()
    }
    
    private func sendToWhisper() {
        guard let url = audioRecorder?.url else { return }
        isProcessing = true
        
        var request = URLRequest(url: whisperURL)
        request.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var data = Data()
        data.append("--\(boundary)\r\n".data(using: .utf8)!)
        data.append("Content-Disposition: form-data; name=\"file\"; filename=\"recording.wav\"\r\n".data(using: .utf8)!)
        data.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        if let audioData = try? Data(contentsOf: url) {
            data.append(audioData)
        }
        data.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        
        URLSession.shared.uploadTask(with: request, from: data) { [weak self] data, response, error in
            DispatchQueue.main.async {
                self?.isProcessing = false
                if let data = data, let result = try? JSONDecoder().decode(WhisperResponse.self, from: data) {
                    self?.transcript = result.text
                    self?.notifyPAT(text: result.text)
                } else if let error = error {
                    print("Whisper upload error: \(error)")
                }
            }
        }.resume()
    }
    
    private func notifyPAT(text: String) {
        // Implementation for sending text to PAT Core API
        print("Heard: \(text)")
    }
    
    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

struct WhisperResponse: Codable {
    let text: String
}
