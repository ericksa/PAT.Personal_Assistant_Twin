import SwiftUI
import AppKit

struct EnhancedOverlayView: View {
    @EnvironmentObject var model: TeleprompterModel
    @StateObject var webSocketManager = WebSocketManager()
    @State private var isDragging = false
    @State private var dragStartPos: CGPoint = .zero
    
    var body: some View {
        VStack(spacing: 20) {
            // Header with controls
            HStack {
                // Connection status indicator
                VStack(alignment: .leading, spacing: 4) {
                    Circle()
                        .fill(webSocketManager.isConnected ? Color.green : Color.red)
                        .frame(width: 10, height: 10)
                    
                    Text(webSocketManager.isConnected ? "Connected" : "Connecting...")
                        .font(.caption)
                        .foregroundColor(.white)
                }
                
                Spacer()
                
                // Control buttons
                HStack(spacing: 8) {
                    Button(action: maximizeWindow) {
                        Image(systemName: "arrow.up.left.and.arrow.down.right")
                            .font(.title3)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .help("Maximize Window")
                    
                    Button(action: minimizeWindow) {
                        Image(systemName: "minus")
                            .font(.title3)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .help("Minimize Window")
                    
                    Button(action: hideWindow) {
                        Image(systemName: "eye.slash.fill")
                            .font(.title3)
                    }
                    .buttonStyle(PlainButtonStyle())
                    .help("Hide Window")
                }
            }
            .padding(.horizontal)
            
            // Main content display with auto-scroll
            ScrollViewReader { scrollView in
                ScrollView {
                    Text(webSocketManager.latestMessage)
                        .font(.system(size: model.fontSize, weight: .medium))
                        .foregroundColor(.white)
                        .multilineTextAlignment(.center)
                        .padding()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .id("scrollTarget")
                }
                .frame(maxHeight: .infinity)
                .onChange(of: webSocketManager.latestMessage) { _ in
                    if model.autoScroll {
                        scrollView.scrollTo("scrollTarget", anchor: .bottom)
                    }
                }
            }
            
            // Enhanced Controls Panel
            VStack(spacing: 12) {
                // Transparency Slider with Percentage
                HStack {
                    Text("Transparency:")
                        .foregroundColor(.white)
                        .font(.caption)
                    
                    Slider(value: $model.opacity, in: 0.1...1.0, step: 0.1)
                    
                    Text("\(Int(model.opacity * 100))%")
                        .foregroundColor(.white)
                        .font(.caption)
                        .frame(width: 40)
                }
                .onChange(of: model.opacity) { newValue in
                    model.savePreferences()
                    if let window = NSApplication.shared.windows.first(where: { $0 is OverlayWindow }) as? OverlayWindow {
                        window.setTransparency(newValue)
                    }
                }
                
                // Font Size Slider
                HStack {
                    Text("Font Size:")
                        .foregroundColor(.white)
                        .font(.caption)
                    
                    Slider(value: $model.fontSize, in: 12...72, step: 2)
                    
                    Text("\(Int(model.fontSize))pt")
                        .foregroundColor(.white)
                        .font(.caption)
                        .frame(width: 40)
                }
                .onChange(of: model.fontSize) { _ in
                    model.savePreferences()
                }
                
                // Advanced Controls Row
                HStack {
                    // Click-Through Toggle
                    Toggle(isOn: $model.clickThrough) {
                        Text("Click-Through")
                            .foregroundColor(.white)
                            .font(.caption)
                    }
                    .onChange(of: model.clickThrough) { newValue in
                        model.savePreferences()
                        if let window = NSApplication.shared.windows.first(where: { $0 is OverlayWindow }) as? OverlayWindow {
                            window.setClickThrough(newValue)
                        }
                    }
                    
                    Spacer()
                    
                    // Auto-Scroll Toggle
                    Toggle(isOn: $model.autoScroll) {
                        Text("Auto-Scroll")
                            .foregroundColor(.white)
                            .font(.caption)
                    }
                }
            }
            .padding(.horizontal)
        }
        .padding()
        .background(Color.clear)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            // WebSocketManager will auto-connect on init
        }
        .onReceive(model.$clickThrough) { newValue in
            // Handle click-through changes
        }
    }
    
    // Window control functions
    private func maximizeWindow() {
        if let window = NSApplication.shared.windows.first(where: { $0 is OverlayWindow }) as? OverlayWindow {
            window.maximizeWindow()
        }
    }
    
    private func minimizeWindow() {
        if let window = NSApplication.shared.windows.first(where: { $0 is OverlayWindow }) as? OverlayWindow {
            window.miniaturize(nil)
        }
    }
    
    private func hideWindow() {
        NSApp.hide(nil)
    }
}

struct EnhancedOverlayView_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedOverlayView()
            .environmentObject(TeleprompterModel())
            .previewLayout(.sizeThatFits)
    }
}