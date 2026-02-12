// ... inside Section("Appearance") ...
Toggle("Dark Mode", isOn: Binding(
    get: { viewModel.useDarkMode },
    set: { newValue in
        viewModel.useDarkMode = newValue
        viewModel.saveSessionSettings()
        #if os(macOS)
        // Apply theme change immediately
        NSApp.appearance = newValue ? NSAppearance(named: .darkAqua) : NSAppearance(named: .aqua)
        #endif
    }
))

