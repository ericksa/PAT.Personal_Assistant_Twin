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
}

export interface Conversation {
  id: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
  context?: Record<string, any>
}