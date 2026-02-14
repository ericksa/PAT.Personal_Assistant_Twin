<template>
  <div class="summary-card" :style="{ borderColor: props.color }">
    <div class="card-header">
      <div class="card-icon">
        <span class="icon">{{ icon }}</span>
        <span 
          class="trend-indicator"
          :class="trend"
          v-if="trend"
        >
          {{ trendIcon }}
        </span>
      </div>
      <div class="card-tooltip">
        <div class="tooltip-trigger">ⓘ</div>
        <div class="tooltip-content">
          {{ helpText }}
        </div>
      </div>
    </div>
    <div class="card-content">
      <h3 class="card-title">{{ title }}</h3>
      <div class="card-value" :style="{ color: props.color }">
        {{ value }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  value: string
  icon: string
  color: string
  trend?: 'up' | 'down' | 'stable'
  helpText?: string
}

const props = withDefaults(defineProps<Props>(), {
  trend: 'stable',
  helpText: ''
})

const trendIcon = computed(() => {
  switch (props.trend) {
    case 'up': return '↑'
    case 'down': return '↓'
    case 'stable': return '→'
    default: return ''
  }
})
</script>

<style scoped>
.summary-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid v-bind(color);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: default;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card-title {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.card-value {
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

.card-icon {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: v-bind('hexToRgba(props.color, 0.1)');
  color: v-bind(color);
}

.trend-indicator {
  font-size: 1rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.trend-indicator.up {
  color: #10b981;
  animation: bounce-up 2s infinite;
}

.trend-indicator.down {
  color: #ef4444;
  animation: bounce-down 2s infinite;
}

.trend-indicator.stable {
  color: #6b7280;
}

@keyframes bounce-up {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

@keyframes bounce-down {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(3px); }
}

.card-tooltip {
  position: relative;
  display: inline-block;
}

.tooltip-trigger {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: help;
  transition: all 0.2s;
}

.tooltip-trigger:hover {
  background: #cbd5e1;
  color: #475569;
}

.tooltip-content {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 125%;
  right: 0;
  width: 200px;
  background: #1e293b;
  color: #f8fafc;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 400;
  line-height: 1.4;
  text-align: center;
  z-index: 10;
  transition: all 0.2s;
  pointer-events: none;
}

.tooltip-content::after {
  content: "";
  position: absolute;
  top: 100%;
  right: 0.375rem;
  border-width: 4px;
  border-style: solid;
  border-color: #1e293b transparent transparent transparent;
}

.card-tooltip:hover .tooltip-content {
  visibility: visible;
  opacity: 1;
}

@media (max-width: 768px) {
  .card-value {
    font-size: 1.5rem;
  }
}

/* Helper function - would need to be computed or external */
.health-status-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
}
</style>

<script>
// These would normally be in a utils file
export function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
</script>