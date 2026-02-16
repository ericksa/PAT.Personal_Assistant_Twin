import Foundation

/// Feature flag configuration for the PAT client.
///
/// The `ThinkConfig` struct holds global flags that control
/// advanced behaviour such as high‑depth reasoning.
/// It is intentionally lightweight so it can be
/// persisted in UserDefaults or a SwiftData model.
public struct ThinkConfig {
    /// Enable the "think" mode which activates deeper
    /// reasoning and longer context windows.
    public static var enabled: Bool = true

    /// Depth level for the think mode.
    /// Possible values: "low", "medium", "high".
    public static var depth: String = "high"
}

// MARK: - Persistence helpers (optional)
extension ThinkConfig {
    private static let defaultsKey = "ThinkConfig"

    /// Load configuration from UserDefaults.
    public static func load() {
        let defaults = UserDefaults.standard
        if let dict = defaults.dictionary(forKey: defaultsKey) {
            enabled = dict["enabled"] as? Bool ?? true
            depth = dict["depth"] as? String ?? "high"
        }
    }

    /// Save configuration to UserDefaults.
    public static func save() {
        let defaults = UserDefaults.standard
        defaults.set(["enabled": enabled, "depth": depth], forKey: defaultsKey)
    }
}
