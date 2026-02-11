import SwiftUI

struct OverlayView: View {
    @State private var displayedText = "Ready for your interview..."
    @State private var isListening = false
    @State private var opacity = 0.9
    @State private var fontSize: CGFloat = 24

    var body: some View {
        VStack(spacing: 20) {
            HStack {
                Button(action: {
                    isListening.toggle()
                }) {
                    Image(systemName: isListening ? "stop.circle.fill" : "play.circle.fill")
                        .font(.title)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer()

                Button(action: {
                    NSApp.hide(nil)
                }) {
                    Image(systemName: "eye.slash.fill")
                        .font(.title)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal)

            ScrollView {
                Text(displayedText)
                    .font(.system(size: fontSize))
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                    .multilineTextAlignment(.center)
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }

            HStack {
                Slider(value: $opacity, in: 0.5...1.0, step: 0.1) {
                    Text("Opacity")
                }

                Slider(value: $fontSize, in: 12...48, step: 2) {
                    Text("Font Size")
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
        .onAppear {
            setupWebSocket()
        }
    }

    private func setupWebSocket() {
        // In a real implementation, this would connect to your backend
        // For now, we'll simulate receiving updates
        Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            if isListening {
                displayedText = "This is a simulated response from PAT. In a real implementation, this would connect to your backend WebSocket at ws://localhost:8005/ws"
            }
        }
    }
}

struct OverlayView_Previews: PreviewProvider {
    static var previews: some View {
        OverlayView()
            .previewLayout(.sizeThatFits)
    }
}