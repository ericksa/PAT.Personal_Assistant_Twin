//
//  ChatViewModel+Extensions.swift
//  PATclient
//
//  Extension methods for ChatViewModel
//

import Foundation

extension ChatViewModel {
    // Helper method for UI checking
    func areServicesHealthy() -> Bool {
        return ollamaStatus == .healthy && agentStatus == .healthy
    }
}
