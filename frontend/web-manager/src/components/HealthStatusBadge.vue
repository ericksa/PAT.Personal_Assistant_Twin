<template>
  <div 
    class="health-status-badge"
    :class="[status, size]"
  >
    <div class="status-dot" :class="status"></div>
    <span v-if="showLabel" class="status-label">{{ statusLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status: 'UP' | 'DOWN' | 'WARNING' | 'PENDING'
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showLabel: false
})

const statusLabel = computed(() => {
  switch (props.status) {
    case 'UP': return 'Healthy'
    case 'DOWN': return 'Down'
    case 'WARNING': return 'Warning'
    case 'PENDING': return 'Checking'
    default: return 'Unknown'
  }
})
</script>

<style scoped>
.health-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.status-dot {
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-dot.UP {
  background: #10b981;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
}

.status-dot.DOWN {
  background: #ef4444;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
}

.status-dot.WARNING {
  background: #f59e0b;
  box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
}

.status-dot.PENDING {
  background: #6b7280;
  box-shadow: 0 0 0 0 rgba(107, 114, 128, 0.7);
  animation: pulse-pending 1.5s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(0, 0, 0, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
  }
}

@keyframes pulse-pending {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.sm .status-dot {
  width: 0.5rem;
  height: 0.5rem;
}

.md .status-dot {
  width: 0.75rem;
  height: 0.75rem;
}

.lg .status-dot {
  width: 1rem;
  height: 1rem;
}

.status-label {
  font-size: 0.875rem;
  color: #475569;
}

.status-label.UP { color: #10b981; }
.status-label.DOWN { color: #ef4444; }
.status-label.WARNING { color: #f59e0b; }
.status-label.PENDING { color: #6b7280; }
</style>