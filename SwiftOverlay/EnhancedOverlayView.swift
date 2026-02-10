import SwiftUI

struct EnhancedOverlayView: View {
    @StateObject private var webSocketManager = WebSocketManager()
    @State private var isListening = true
    @State private var opacity = 0.9
    @State private var fontSize: CGFloat = 24
    @State private var isDragging = false
    @State private var dragOffset = CGSize.zero

    var body: some View {
        VStack(spacing: 20) {
            HStack {
                // Connection status indicator
                Circle()
                    .fill(webSocketManager.isConnected ? Color.green : Color.red)
                    .frame(width: 10, height: 10)

                Text(webSocketManager.isConnected ? "Connected" : "Connecting...")
                    .font(.caption)

                Spacer()

                // Control buttons
                Button(action: {
                    NSApp.hide(nil)
                }) {
                    Image(systemName: "eye.slash.fill")
                        .font(.title2)
                }
                .buttonStyle(PlainButtonStyle())
                .help("Hide window")
            }
            .padding(.horizontal)

            // Main content display
            ScrollView {
                Text(webSocketManager.latestMessage)
                    .font(.system(size: fontSize))
                    .fontWeight(.medium)
                    .multilineTextAlignment(.center)
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .frame(maxHeight: .infinity)

            // Controls
            VStack(spacing: 10) {
                HStack {
                    Text("Opacity:")
                    Slider(value: $opacity, in: 0.3...1.0, step: 0.1)
                    Text(String(format: "%.1f", opacity))
                }

                HStack {
                    Text("Font Size:")
                    Slider(value: $fontSize, in: 12...48, step: 2)
                    Text("\(Int(fontSize))pt")
                }
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.thinMaterial)
        .cornerRadius(16)
        .shadow(radius: 10)
        .opacity(opacity)
        .frame(width: 600, height: 400)
        .offset(dragOffset)
        .gesture(
            DragGesture()
                .onChanged { gesture in
                    dragOffset = gesture.translation
                }
                .onEnded { _ in
                    dragOffset = .zero
                }
        )
        .onAppear {
            // Send periodic pings to keep connection alive
            Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
                if webSocketManager.isConnected {
                    webSocketManager.sendPing()
                }
            }
        }
    }
}

struct EnhancedOverlayView_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedOverlayView()
            .previewLayout(.sizeThatFits)
    }
}