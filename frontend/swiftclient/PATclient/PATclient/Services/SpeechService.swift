//
//  SpeechService.swift
//  PATclient
//
//  Adapted from Enchanted app for PAT client
//

import Foundation
import AVFoundation
import SwiftUI


class SpeechSynthesizerDelegate: NSObject, AVSpeechSynthesizerDelegate {
    var onSpeechFinished: (() -> Void)?
    var onSpeechStart: (() -> Void)?
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        onSpeechFinished?()
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        onSpeechStart?()
    }
    
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didReceiveError error: Error, for utterance: AVSpeechUtterance, at characterIndex: UInt) {
        print("Speech synthesis error: \(error)")
    }
}

@MainActor final class SpeechService: NSObject, ObservableObject {
    static let shared = SpeechService()
    private let synthesizer = AVSpeechSynthesizer()
    private let delegate = SpeechSynthesizerDelegate()
    
    @Published var isSpeaking = false
    @Published var voices: [AVSpeechSynthesisVoice] = []
    @Published var isEnabled: Bool = false
    
    override init() {
        super.init()
        synthesizer.delegate = delegate
        fetchVoices()
    }
    
    func getVoiceIdentifier() -> String? {
        let voiceIdentifier = UserDefaults.standard.string(forKey: "patVoiceIdentifier")
        if let voice = voices.first(where: {$0.identifier == voiceIdentifier}) {
            return voice.identifier
        }
        
        return voices.first?.identifier
    }
    
    var lastCancellation: (() -> Void)? = {}
    
    func speak(text: String, onFinished: @escaping () -> Void = {}) {
        guard isEnabled else { return }
        
        guard let voiceIdentifier = getVoiceIdentifier() else {
            print("Could not find voice identifier")
            return
        }
        
        print("Using voice: \(voiceIdentifier)")
        
        if synthesizer.isSpeaking {
            Task {
                await stopSpeaking()
            }
        }
        
        lastCancellation = onFinished
        delegate.onSpeechFinished = { [weak self] in
            Task { @MainActor in
                self?.isSpeaking = false
                onFinished()
            }
        }
        delegate.onSpeechStart = { [weak self] in
            Task { @MainActor in
                self?.isSpeaking = true
            }
        }
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(identifier: voiceIdentifier)
        utterance.rate = 0.5
        utterance.pitchMultiplier = 1.0
        utterance.volume = 1.0
        
        synthesizer.speak(utterance)
    }
    
    func stopSpeaking() {
        isSpeaking = false
        lastCancellation?()
        synthesizer.stopSpeaking(at: .immediate)
    }
    
    func fetchVoices() {
        let voices = AVSpeechSynthesisVoice.speechVoices().sorted { (firstVoice: AVSpeechSynthesisVoice, secondVoice: AVSpeechSynthesisVoice) -> Bool in
            return firstVoice.quality.rawValue > secondVoice.quality.rawValue
        }
        
        let diff = self.voices.elementsEqual(voices, by: { $0.identifier == $1.identifier })
        if diff {
            return
        }
        
        DispatchQueue.main.async {
            self.voices = voices
        }
    }
    
    func setVoice(identifier: String) {
        UserDefaults.standard.set(identifier, forKey: "patVoiceIdentifier")
    }
    
    func setEnabled(_ enabled: Bool) {
        isEnabled = enabled
        UserDefaults.standard.set(enabled, forKey: "patSpeechEnabled")
    }
}
