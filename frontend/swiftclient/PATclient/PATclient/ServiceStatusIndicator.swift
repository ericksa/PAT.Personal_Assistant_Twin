import SwiftUI

// MARK: - Service Status Indicator
/// A native macOS-style service status indicator with translucent sidebar appearance
struct ServiceStatusIndicator: View {
    @ObservedObject var viewModel: ChatViewModel
    @State private var isExpanded: Bool = false
    @State private var showDetails: Bool = false

    var body: some View {
        VStack(spacing: 0) {
            // Compact status bar
            HStack(spacing: 12) {
                // Overall status
                statusIndicator(
                    title: "Services",
                    icon: "network",
                    status: overallStatus,
                    isHealthy: viewModel.areServicesHealthy()
                )

                Divider()
                    .frame(height: 16)

                // Individual services
                serviceStatusDot(
                    icon: "desktopcomputer",
                    name: "PAT Core",
                    status: viewModel.patCoreStatus
                )

                serviceStatusDot(
                    icon: "bubble.left.and.bubble.right",
                    name: "Agent",
                    status: viewModel.agentStatus
                )

                serviceStatusDot(
                    icon: "arrow.up.arrow.down",
                    name: "Ingest",
                    status: viewModel.ingestStatus
                )

                serviceStatusDot(
                    icon: "brain.head.profile",
                    name: "LLM",
                    status: viewModel.ollamaStatus
                )

                Spacer()

                // Expand/collapse button
                Button(action: { withAnimation(.easeInOut(duration: 0.2)) { isExpanded.toggle() } }) {
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.borderless)

                // Refresh button
                Button(action: { Task { await viewModel.checkAllServices() } }) {
                    Image(systemName: "arrow.clockwise")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.borderless)
                .help("Refresh service status")
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(.ultraThinMaterial)

            // Expanded details panel
            if isExpanded {
                VStack(alignment: .leading, spacing: 12) {
                    // Service details grid
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ServiceDetailCard(
                            title: "PAT Core",
                            icon: "desktopcomputer",
                            status: viewModel.patCoreStatus,
                            endpoint: Config.patCoreBaseURL,
                            features: ["Calendar", "Tasks", "Emails"]
                        )

                        ServiceDetailCard(
                            title: "Agent",
                            icon: "bubble.left.and.bubble.right",
                            status: viewModel.agentStatus,
                            endpoint: Config.agentBaseURL,
                            features: ["Chat", "Memory", "RAG Search"]
                        )

                        ServiceDetailCard(
                            title: "Ingest",
                            icon: "arrow.up.arrow.down",
                            status: viewModel.ingestStatus,
                            endpoint: Config.ingestBaseURL,
                            features: ["Document Upload", "Resume Upload", "Vector Search"]
                        )

                        ServiceDetailCard(
                            title: "LLM",
                            icon: "brain.head.profile",
                            status: viewModel.ollamaStatus,
                            endpoint: viewModel.llmProvider == "lmstudio" ? Config.lmStudioBaseURL : Config.ollamaBaseURL,
                            features: viewModel.llmProvider == "lmstudio" ? ["LM Studio", "GLM-4.6v-flash"] : ["Ollama", "Local Models"]
                        )
                    }
                    .padding(.horizontal, 16)

                    // Health details from agent
                    if let health = viewModel.agentHealthDetails {
                        Divider()
                            .padding(.horizontal, 16)

                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Image(systemName: "heart.text.square.fill")
                                    .foregroundColor(.accentColor)
                                Text("Agent Health Details")
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                Spacer()
                            }

                            HStack(spacing: 16) {
                                HealthDetailItem(
                                    label: "Database",
                                    status: health.services.database,
                                    icon: "cylinder"
                                )
                                HealthDetailItem(
                                    label: "Redis",
                                    status: health.services.redis,
                                    icon: "memorychip"
                                )
                                HealthDetailItem(
                                    label: "Ingest",
                                    status: health.services.ingest,
                                    icon: "arrow.up.arrow.down"
                                )
                                HealthDetailItem(
                                    label: "LLM Provider",
                                    status: health.services.llm_provider,
                                    icon: "brain.head.profile"
                                )
                            }
                        }
                        .padding(.horizontal, 16)
                    }

                    // Quick actions
                    if !viewModel.areServicesHealthy() {
                        Divider()
                            .padding(.horizontal, 16)

                        HStack(spacing: 12) {
                            Text("Troubleshooting:")
                                .font(.caption)
                                .foregroundColor(.secondary)

                            Spacer()

                            Button(action: { Task { await viewModel.checkAllServices() } }) {
                                Label("Check Again", systemImage: "arrow.clockwise")
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.small)
                        }
                        .padding(.horizontal, 16)
                    }
                }
                .padding(.vertical, 12)
                .background(.ultraThinMaterial)
            }
        }
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: isExpanded ? 12 : 0, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: isExpanded ? 12 : 0, style: .continuous)
                .stroke(Color.secondary.opacity(0.1), lineWidth: 1)
        )
        .padding(.horizontal, isExpanded ? 12 : 0)
        .padding(.vertical, isExpanded ? 8 : 0)
    }

    private var overallStatus: ServiceStatus {
        if viewModel.areServicesHealthy() {
            return .healthy
        }
        return .disconnected
    }

    // MARK: - Status Indicator View
    @ViewBuilder
    private func statusIndicator(title: String, icon: String, status: ServiceStatus, isHealthy: Bool) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(isHealthy ? .green : .orange)

            Text(title)
                .font(.caption)
                .fontWeight(.medium)

            Circle()
                .fill(isHealthy ? Color.green : Color.orange)
                .frame(width: 8, height: 8)
                .overlay(
                    Circle()
                        .stroke(isHealthy ? Color.green.opacity(0.3) : Color.orange.opacity(0.3), lineWidth: 2)
                )
        }
    }

    // MARK: - Service Status Dot
    @ViewBuilder
    private func serviceStatusDot(icon: String, name: String, status: ServiceStatus) -> some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption2)
                .foregroundColor(status.color)

            Circle()
                .fill(status.color)
                .frame(width: 6, height: 6)
        }
        .help("\(name): \(status.displayText)")
    }
}

// MARK: - Service Detail Card
struct ServiceDetailCard: View {
    let title: String
    let icon: String
    let status: ServiceStatus
    let endpoint: String
    let features: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundColor(status.color)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.subheadline)
                        .fontWeight(.semibold)

                    HStack(spacing: 4) {
                        Circle()
                            .fill(status.color)
                            .frame(width: 6, height: 6)
                        Text(status.displayText)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()
            }

            Text(endpoint)
                .font(.caption2)
                .foregroundColor(.secondary)
                .lineLimit(1)

            HStack(spacing: 6) {
                ForEach(features, id: \.self) { feature in
                    FeatureTag(name: feature)
                }
            }
        }
        .padding(12)
        .background(Color.secondary.opacity(0.05))
        .cornerRadius(8)
    }
}

// MARK: - Feature Tag
struct FeatureTag: View {
    let name: String

    var body: some View {
        Text(name)
            .font(.caption2)
            .fontWeight(.medium)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(Color.accentColor.opacity(0.1))
            .foregroundColor(.accentColor)
            .cornerRadius(4)
    }
}

// MARK: - Health Detail Item
struct HealthDetailItem: View {
    let label: String
    let status: String
    let icon: String

    var isActive: Bool {
        status == "active" || status == "healthy"
    }

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.caption2)
                .foregroundColor(isActive ? .green : .red)

            VStack(alignment: .leading, spacing: 1) {
                Text(label)
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Text(status.capitalized)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(isActive ? .green : .red)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - Native Sidebar Style
/// A view modifier that applies native macOS sidebar styling
struct NativeSidebarStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial)
            .overlay(
                Rectangle()
                    .fill(Color.secondary.opacity(0.1))
                    .frame(width: 1)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            )
    }
}

extension View {
    func nativeSidebar() -> some View {
        modifier(NativeSidebarStyle())
    }
}

// MARK: - Native Toolbar Style
/// A view modifier that applies native macOS toolbar styling
struct NativeToolbarStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial)
            .overlay(
                Rectangle()
                    .fill(Color.secondary.opacity(0.1))
                    .frame(height: 1)
                    .frame(maxHeight: .infinity, alignment: .bottom)
            )
    }
}

extension View {
    func nativeToolbar() -> some View {
        modifier(NativeToolbarStyle())
    }
}
