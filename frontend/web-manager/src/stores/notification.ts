import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification } from '@/types'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  
  function addNotification(notification: Omit<Notification, 'id' | 'timestamp'>) {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date()
    }
    
    notifications.value.push(newNotification)
    
    // Auto-remove non-persistent notifications after 5 seconds
    if (!notification.persistent) {
      setTimeout(() => {
        removeNotification(newNotification.id)
      }, 5000)
    }
    
    return newNotification.id
  }
  
  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  function clearAll() {
    notifications.value = []
  }
  
  // Convenience methods for different notification types
  function success(message: string, persistent?: boolean) {
    return addNotification({ type: 'success', message, persistent })
  }
  
  function error(message: string, persistent: boolean = true) {
    return addNotification({ type: 'error', message, persistent })
  }
  
  function warning(message: string, persistent?: boolean) {
    return addNotification({ type: 'warning', message, persistent })
  }
  
  function info(message: string, persistent?: boolean) {
    return addNotification({ type: 'info', message, persistent })
  }
  
  const errors = computed(() => notifications.value.filter(n => n.type === 'error'))
  const warnings = computed(() => notifications.value.filter(n => n.type === 'warning'))
  const hasErrors = computed(() => errors.value.length > 0)
  const hasWarnings = computed(() => warnings.value.length > 0)
  
  return {
    notifications,
    addNotification,
    removeNotification,
    clearAll,
    success,
    error,
    warning,
    info,
    errors,
    warnings,
    hasErrors,
    hasWarnings
  }
})