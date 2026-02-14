# PAT macOS Client UI/UX Improvements

## Summary of Changes

This document summarizes the improvements made to the PAT macOS Swift client to create a more native macOS experience, connect to LM Studio's GLM-4.6v-flash model, and expose underutilized features.

---

## 1. Native macOS Styling

### Visual Design
- **Translucent sidebars**: Applied `.ultraThinMaterial` background to all sidebar components
- **SF Symbols integration**: Replaced custom icons with appropriate SF Symbols throughout the app
- **Native button styles**: Used `.borderless` and `.bordered` button styles consistently
- **Modern toggle styles**: Implemented `.checkbox` toggle style for macOS
- **Native toolbar**: Added `.nativeToolbar()` modifier for consistent toolbars
- **Material backgrounds**: Used `.ultraThinMaterial` for toolbars and header areas

### Components Updated
- **SessionListView**: Added search functionality, improved row layout with icons
- **ChatView**: New empty state design, improved message input area
- **CalendarView**: Sidebar with event filtering, modern event row design
- **TasksView**: Status filter sidebar, modern task row with actions
- **EmailsView**: Folder sidebar with unread counts, modern email list

### Navigation
- **NavigationSplitView**: Used throughout for master-detail layouts
- **Three-pane layout**: EmailsView now uses triple-pane NavigationSplitView
- **Improved column widths**: Set appropriate min/ideal widths for sidebars

---

## 2. LM Studio Integration

### New Files

#### `LMStudioService.swift`
- OpenAI-compatible API client for LM Studio
- Supports GLM-4.6v-flash and other OpenAI-compatible models
- Model listing via `/v1/models` endpoint
- Chat completions via `/v1/chat/completions`
- Health check functionality

#### Config Update
```swift
static let lmStudioBaseURL = "http://localhost:1234/v1"
```

### LLM Provider Support

#### `LLMProvider` Enum
```swift
enum LLMProvider: String, CaseIterable, Identifiable {
    case ollama = "ollama"
    case lmstudio = "lmstudio"
    
    var displayName: String { ... }
    var icon: String { ... }
}
```

### Service Improvements
- **Provider selector**: Added to toolbar in ChatView
- **Model selection**: Picker for available models from active provider
- **Unified service**: `UnifiedLLMService` manages both Ollama and LM Studio

---

## 3. Service Status Indicator

### New Component: `ServiceStatusIndicator.swift`

#### Features
- **Collapsible panel**: Expand/collapse with animation
- **Individual service status**: PAT Core, Agent, Ingest, LLM (Ollama + LM Studio)
- **Health details**: Shows Agent's internal service statuses
- **Quick actions**: Refresh button, troubleshooting steps
- **Visual indicators**: Color-coded status dots and icons

#### Service Detail Card
```swift
ServiceDetailCard(
    title: "PAT Core",
    icon: "desktopcomputer",
    status: viewModel.patCoreStatus,
    endpoint: Config.patCoreBaseURL,
    features: ["Calendar", "Tasks", "Emails"]
)
```

#### Status Colors
- 🟢 Green: Healthy
- 🔴 Red: Disconnected
- 🟠 Orange: Error

---

## 4. Enhanced Settings

### New Settings Structure
SettingsView now has 4 tabs:
1. **General**: Appearance, behavior settings
2. **LLM**: Provider selection, model picker, endpoint display
3. **Services**: Visual service status with endpoints
4. **Advanced**: Toggles, export options, debug tools

### LLM Provider Settings
- Radio group for Ollama vs LM Studio
- Model dropdown with refresh
- Endpoint display (non-editable)
- Status indicator for selected provider

---

## 5. Underutilized Features Exposed

### Tasks View Enhancements
- **Status sidebar**: Filter by pending, in-progress, completed
- **Quick actions**: AI suggestions, sync, focus tasks
- **Priority indicator**: Visual bars for task priority
- **Tag display**: Show task tags inline
- **Stats footer**: Task counts by status
- **Actions menu**: Edit, complete, delete per task

### Calendar View Enhancements
- **Sidebar with sections**: Today, Upcoming
- **Event type badges**: Color-coded by type
- **Quick navigation**: Previous/Next day buttons
- **Priority indicators**: Exclamation marks for urgent events
- **Stats badges**: Event counts in footer
- **Modern event row**: Time column, location display

### Emails View Enhancements
- **Three-pane layout**: Folders, list, detail
- **Folder sidebar**: With unread counts
- **Search bar**: Real-time filtering
- **Category badges**: Color-coded categories
- **AI classify action**: In context menu
- **Email analytics**: Unread/urgent/flagged counts
- **Priority indicators**: Visual markers for important emails

### Chat View Enhancements
- **Service status bar**: Always visible at top
- **Provider selector**: In toolbar
- **Model picker**: In input area
- **Feature cards**: In empty state (RAG, Web Search, Calendar, Tasks)
- **Improved empty state**: With setup instructions
- **Better error banner**: With dismiss button

---

## 6. Backend Integration Updates

### AgentService Updates
```swift
func query(
    text: String,
    webSearch: Bool,
    useMemory: Bool = true,
    userId: String = "default",
    stream: Bool = false,
    llmProvider: String = "ollama",
    model: String? = nil
) async throws -> QueryResponse
```

### QueryRequest Updates
Added fields:
- `llm_provider`: "ollama" or "lmstudio"
- `model`: Selected model name

### ChatViewModel Updates
- Added `lmStudioStatus` published property
- Updated `areServicesHealthy()` to check correct provider
- Modified `checkAllServices()` to check based on selected provider
- Added `refreshAvailableModels()` with provider-specific logic

---

## 7. New Reusable Components

### EmptyStateView
```swift
EmptyStateView(
    icon: "calendar.badge.exclamationmark",
    title: "No Events",
    message: "Your calendar is empty"
)
```

### LoadingView
```swift
LoadingView(message: "Loading events...")
```

### FeatureCard (Chat empty state)
```swift
FeatureCard(
    icon: "doc.text.magnifyingglass",
    title: "RAG Search",
    description: "Search your documents"
)
```

### View Modifiers
```swift
.nativeSidebar()    // Applies ultraThinMaterial + sidebar styling
.nativeToolbar()     // Applies ultraThinMaterial + toolbar styling
```

---

## 8. Keyboard Shortcuts

### Added Shortcuts
- `Cmd+N`: New chat
- `Cmd+Enter`: Send message
- `Esc`: Close settings

---

## File Changes Summary

### New Files
1. `LMStudioService.swift` - LM Studio API client
2. `ServiceStatusIndicator.swift` - Service health UI component

### Modified Files
1. `Config.swift` - Added LM Studio URL
2. `ChatView.swift` - Native styling, service indicator
3. `ChatViewModel.swift` - LLM provider support, health checking
4. `AgentService.swift` - Added llm_provider and model parameters
5. `SessionListView.swift` - Search, native sidebar
6. `SettingsView.swift` - Tabbed interface, LLM settings
7. `CalendarView.swift` - Native sidebar, modern layout
8. `TasksView.swift` - Sidebar filters, modern rows
9. `EmailsView.swift` - Three-pane layout, native styling
10. `MessageRow.swift` - Updated source icon logic

---

## Backend Requirements

To use the LM Studio integration:

1. **LM Studio must be running** on localhost:1234
2. **Load GLM-4.6v-flash model** (or another OpenAI-compatible model)
3. **Agent service must support** `llm_provider` and `model` parameters in `/query` endpoint

### Example Agent Request
```json
{
  "query": "Hello",
  "user_id": "default",
  "stream": false,
  "tools": [],
  "llm_provider": "lmstudio",
  "model": "GLM-4.6v-flash"
}
```

---

## Design Principles Applied

1. **macOS Human Interface Guidelines**: Followed spacing, typography, and interaction patterns
2. **Visual Hierarchy**: Clear distinction between primary and secondary actions
3. **Progressive Disclosure**: Advanced features in expandable sections
4. **Feedback**: Status indicators for all background operations
5. **Efficiency**: Keyboard shortcuts and quick actions exposed
6. **Consistency**: Same patterns across all views

---

## Next Steps

1. Test with actual LM Studio instance running GLM-4.6v-flash
2. Verify Agent service accepts llm_provider parameter
3. Consider adding more granular service health monitoring
4. Add persistence for user's LLM provider preference
5. Consider adding keyboard shortcuts for common actions

---

*Last Updated: February 13, 2026*
