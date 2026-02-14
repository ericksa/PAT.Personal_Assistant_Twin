export interface ServiceStatus {
  name: string
  status: 'UP' | 'DOWN' | 'WARNING' | 'PENDING'
  message: string
  lastChecked: Date
  responseTime?: number
  error?: string
  endpoint?: string
  version?: string
  uptime?: string
}

export interface ResourceUsage {
  cpu: number
  memory: number
  disk: number
  timestamp: Date
  processes?: Array<{
    name: string
    cpu: number
    memory: number
    pid?: number
  }>
}

export interface BackendService {
  id: string
  name: string
  displayName: string
  description: string
  endpoint: string
  healthEndpoint: string
  metricsEndpoint?: string
  category: 'core' | 'ingestion' | 'processing' | 'interface'
  icon: string
  color: string
}

export interface ServiceMetrics {
  cpu_usage: number
  memory_usage: number
  memory_total_mb: number
  memory_used_mb: number
  uptime_seconds: number
  request_count: number
  error_count: number
  avg_response_time_ms: number
  timestamp: string
}

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  version?: string
  uptime?: string
  checks: Array<{
    name: string
    status: 'healthy' | 'unhealthy'
    message?: string
    response_time_ms?: number
  }>
}

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  timestamp: Date
  persistent?: boolean
}

export interface QuickAction {
  id: string
  name: string
  description: string
  icon: string
  color: string
  action: () => Promise<void>
  successMessage?: string
  errorMessage?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  context?: Record<string, any>
}

export interface ChatResponse {
  message: string
  conversation_id?: string
  actions?: Action[]
  suggestions?: string[]
}

export interface Action {
  type: string
  status: 'pending' | 'completed' | 'failed'
  description: string
  data?: Record<string, any>
  results?: Record<string, any>
  error?: string
}

export interface Conversation {
  id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  context?: Record<string, any>
}