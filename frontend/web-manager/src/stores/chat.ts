import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatRequest, ChatResponse, Action, Conversation } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const currentConversation = ref<Conversation | null>(null)
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const streaming = ref(false)

  const isActive = computed(() => currentConversation.value !== null)
  const messages = computed(() => currentConversation.value?.messages || [])
  const lastAction = computed(() => {
    if (!currentConversation.value) return null
    const lastMsg = currentConversation.value.messages[currentConversation.value.messages.length - 1]
    return lastMsg?.role === 'assistant' ? lastMsg : null
  })

  async function startConversation(context?: Record<string, any>) {
    loading.value = true
    error.value = null
    
    try {
      // Send a greeting message to start the conversation
      const response = await sendMessage("Hello! How can I help you with tasks, reminders, calendar, or email today?", context)
      
      if (response.conversation_id) {
        // Get the conversation
        const convResponse = await fetch(`http://localhost:8888/api/chat/conversations/${response.conversation_id}`)
        currentConversation.value = await convResponse.json()
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start conversation'
      console.error('Failed to start conversation:', e)
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(message: string, context?: Record<string, any>): Promise<ChatResponse> {
    if (!currentConversation.value && !context) {
      throw new Error('No active conversation')
    }

    loading.value = true
    error.value = null
    streaming.value = true
    
    try {
      const request: ChatRequest = {
        message,
        conversation_id: currentConversation.value?.id,
        context
      }

      const response = await fetch('http://localhost:8888/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`Chat error: ${response.statusText}`)
      }

      const chatResponse = await response.json()
      
      // Update current conversation
      if (!currentConversation.value) {
        await loadConversation(chatResponse.conversation_id)
      } else {
        // Refresh conversation to get full message history
        await loadConversation(currentConversation.value.id)
      }
      
      return chatResponse
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to send message'
      throw e
    } finally {
      loading.value = false
      streaming.value = false
    }
  }

  async function loadConversation(conversationId: string) {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`http://localhost:8888/api/chat/conversations/${conversationId}`)
      
      if (!response.ok) {
        throw new Error(`Failed to load conversation: ${response.statusText}`)
      }
      
      currentConversation.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load conversation'
      console.error('Failed to load conversation:', e)
    } finally {
      loading.value = false
    }
  }

  async function executeAction(action: Action): Promise<boolean> {
    try {
      const response = await fetch('http://localhost:8888/api/chat/execute-action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({...action} as any) // Cast to any for compatibility
      })

      if (!response.ok) {
        throw new Error(`Action error: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Update action status
      if (result.success) {
        action.status = 'completed'
        action.data = result.result
      } else {
        action.status = 'failed'
      }
      
      return result.success
    } catch (e) {
      console.error('Failed to execute action:', e)
      action.status = 'failed'
      return false
    }
  }

  async function clearConversation() {
    if (currentConversation.value?.id) {
      try {
        await fetch(`http://localhost:8888/api/chat/conversations/${currentConversation.value.id}`, {
          method: 'DELETE'
        })
      } catch (e) {
        console.error('Failed to delete conversation:', e)
      }
    }
    currentConversation.value = null
  }

  async function listAllConversations() {
    try {
      const response = await fetch('http://localhost:8888/api/chat/conversations')
      
      if (!response.ok) {
        throw new Error(`Failed to list conversations: ${response.statusText}`)
      }
      
      conversations.value = await response.json()
    } catch (e) {
      console.error('Failed to list conversations:', e)
    }
  }

  async function deleteConversation(conversationId: string) {
    try {
      await fetch(`http://localhost:8888/api/chat/conversations/${conversationId}`, {
        method: 'DELETE'
      })
      
      // Remove from list
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      
      // If this was the current conversation, clear it
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = null
      }
    } catch (e) {
      console.error('Failed to delete conversation:', e)
    }
  }

  return {
    currentConversation,
    conversations,
    loading,
    error,
    streaming,
    isActive,
    messages,
    lastAction,
    startConversation,
    sendMessage,
    loadConversation,
    executeAction,
    clearConversation,
    listAllConversations,
    deleteConversation
  }
})