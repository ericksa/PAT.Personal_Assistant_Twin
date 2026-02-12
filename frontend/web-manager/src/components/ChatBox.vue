<template>
  <div class="chat-container">
    <!-- Conversation Header -->
    <div class="chat-header">
      <h3 class="font-semibold text-lg">AI Assistant</h3>
      <button
        @click="clearConversation"
        class="text-sm text-gray-500 hover:text-red-500"
        title="Clear conversation"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>

    <!-- Messages Display -->
    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.role]"
      >
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ message.role === 'user' ? 'You' : 'AI Assistant' }}</span>
            <span v-if="message.timestamp" class="message-timestamp">
              {{ formatTime(message.timestamp) }}
            </span>
          </div>
          <div class="message-body">{{ message.content }}</div>
        </div>
      </div>

      <!-- Loading Indicator -->
      <div v-if="loading" class="message assistant">
        <div class="message-content">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions Panel (if any actions are detected) -->
    <div v-if="lastAction" class="actions-panel">
      <div class="action-card">
        <div class="action-header">
          <span class="action-icon">⚡</span>
          <span>Action Detected</span>
        </div>
        <div class="action-body">
          <p>{{ lastAction.type.replace('_', ' ').toUpperCase() }}</p>
          <p v-if="lastAction.description" class="text-sm text-gray-600">{{ lastAction.description }}</p>
        </div>
        <div class="action-footer">
          <button
            @click="executeAction(lastAction)"
            :disabled="lastAction.status !== 'pending'"
            class="execute-button"
            :class="lastAction.status"
          >
            <span v-if="lastAction.status === 'pending'">Execute</span>
            <span v-else-if="lastAction.status === 'completed'">✓ Done</span>
            <span v-else-if="lastAction.status === 'failed'">✗ Failed</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Message Input -->
    <div class="chat-input">
      <textarea
        v-model="userMessage"
        @keypress.enter.prevent="sendMessage"
        placeholder="Ask me about tasks, calendar, email, or reminders..."
        :disabled="loading"
        ref="messageInput"
        rows="1"
        class="message-input"
      ></textarea>
      <button
        @click="sendMessage"
        :disabled="!userMessage.trim() || loading"
        class="send-button"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { Action } from '@/types/chat'

const chatStore = useChatStore()
const messagesContainer = ref<HTMLElement>()
const messageInput = ref<HTMLElement>()
const userMessage = ref('')

const messages = computed(() => chatStore.messages)
const loading = computed(() => chatStore.loading || chatStore.streaming)
const error = computed(() => chatStore.error)
const lastAction = computed(() => chatStore.lastAction)

// Auto-scroll to bottom when messages change
watch(messages, async () => {
  await nextTick()
  scrollToBottom()
}, { deep: true })

onMounted(async () => {
  await chatStore.startConversation({
    available_services: ['tasks', 'calendar', 'email', 'reminders']
  })
  
  // Focus input
  if (messageInput.value) {
    messageInput.value.focus()
  }
})

onUnmounted(() => {
  // Clean up if needed
})

async function sendMessage() {
  const message = userMessage.value.trim()
  if (!message || loading.value) return

  userMessage.value = ''
  
  try {
    await chatStore.sendMessage(message, {
      available_services: ['tasks', 'calendar', 'email', 'reminders'],
      current_datetime: new Date().toISOString()
    })
  } catch (e) {
    console.error('Failed to send message:', e)
  }
}

async function executeAction(action: Action) {
  try {
    await chatStore.executeAction(action)
  } catch (e) {
    console.error('Failed to execute action:', e)
  }
}

async function clearConversation() {
  await chatStore.clearConversation()
  await chatStore.startConversation({
    available_services: ['tasks', 'calendar', 'email', 'reminders']
  })
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.chat-header {
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
}

.message.user .message-content {
  background: #007bff;
  color: white;
}

.message.assistant .message-content {
  background: #f8f9fa;
  color: #212529;
  border: 1px solid #e9ecef;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.message.user .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.message.assistant .message-header {
  color: #6c757d;
}

.message-timestamp {
  font-size: 0.7rem;
  opacity: 0.7;
}

.message-body {
  white-space: pre-wrap;
  line-height: 1.5;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6c757d;
  display: inline-block;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* Actions Panel */
.actions-panel {
  padding: 0 20px 16px 20px;
}

.action-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: #495057;
}

.action-icon {
  font-size: 1.2rem;
}

.action-body p:first-child {
  margin-bottom: 4px;
  text-transform: uppercase;
  font-weight: 600;
  color: #212529;
}

.action-footer {
  margin-top: 12px;
  text-align: right;
}

.execute-button {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.execute-button.pending {
  background: #007bff;
  color: white;
}

.execute-button.pending:hover:not(:disabled) {
  background: #0056b3;
}

.execute-button.pending:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.execute-button.completed {
  background: #28a745;
  color: white;
}

.execute-button.failed {
  background: #dc3545;
  color: white;
}

/* Chat Input */
.chat-input {
  padding: 16px 20px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ced4da;
  border-radius: 20px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5;
  max-height: 120px;
  transition: border-color 0.15s ease-in-out;
}

.message-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.15);
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  padding: 10px 12px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-button:not(:disabled):hover {
  background: #0056b3;
  transform: scale(1.05);
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Responsive Design */
@media (max-width: 768px) {
  .chat-container {
    border-radius: 0;
    height: 100vh;
    border: none;
  }
}
</style>