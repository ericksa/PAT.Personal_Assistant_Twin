<template>
  <div class="service-card" :class="statusClass">
    <div class="card-header">
      <div class="service-info">
        <div 
          class="service-icon" 
          :style="{ backgroundColor: hexToRgba(service.color, 0.1), color: service.color }"
        >
          {{ service.icon }}
        </div>
        <div class="service-details">
          <h3 class="service-name">{{ service.displayName }}</h3>
          <p class="service-description">{{ service.description }}</p>
        </div>
      </div>
      <HealthStatusBadge :status="serviceStatus" size="md" />
    </div>

    <div class="card-body">
      <!-- Version and Uptime -->
      <div class="service-meta" v-if="serviceStatus === 'UP'">
        <div class="meta-item" v-if="health?.version">
          <span class="meta-label">Version</span>
          <span class="meta-value">{{ health.version }}</span>
        </div>
        <div class="meta-item" v-if="serviceMetrics?.uptime_seconds">
          <span class="meta-label">Uptime</span>
          <span class="meta-value">{{ formatUptime(serviceMetrics.uptime_seconds) }}</span>
        </div>
      </div>

      <!-- Metrics -->
      <div class="service-metrics" v-if="serviceMetrics">
        <div class="metric-list">
          <div class="metric-item">
            <span class="metric-label">CPU</span>
            <div class="metric-value">
              <span class="metric-number">{{ Math.round(serviceMetrics.cpu_usage) }}%</span>
              <div class="metric-bar">
                <div 
                  class="metric-fill" 
                  :style="{ 
                    width: `${Math.round(serviceMetrics.cpu_usage)}%`,
                    backgroundColor: getMetricColor(serviceMetrics.cpu_usage, 'cpu')
                  }"
                ></div>
              </div>
            </div>
          </div>

          <div class="metric-item">
            <span class="metric-label">Memory</span>
            <div class="metric-value">
              <span class="metric-number">
                {{ formatBytes(serviceMetrics.memory_used_mb * 1024 * 1024) }}
              </span>
              <div class="metric-bar">
                <div 
                  class="metric-fill" 
                  :style="{ 
                    width: `${Math.round(serviceMetrics.memory_usage)}%`,
                    backgroundColor: getMetricColor(serviceMetrics.memory_usage, 'memory')
                  }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Response Time -->
          <div class="metric-item">
            <span class="metric-label">Response</span>
            <div class="metric-value">
              <span class="metric-number">
                {{ Math.round(serviceMetrics.avg_response_time_ms) }}ms
              </span>
              <div class="metric-bar">
                <div 
                  class="metric-fill" 
                  :style="{ 
                    width: `${Math.min(Math.round(serviceMetrics.avg_response_time_ms / 10), 100)}%`,
                    backgroundColor: getMetricColor(serviceMetrics.avg_response_time_ms, 'response')
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div class="service-error" v-else-if="service.error || service.message">
        <div class="error-icon">⚠️</div>
        <div class="error-message">
          {{ service.error || service.message }}
        </div>
      </div>

      <!-- Endpoint -->
      <div class="service-endpoint">
        <span class="endpoint-label">Endpoint:</span>
        <span class="endpoint-value">{{ service.endpoint }}</span>
      </div>
    </div>

    <!-- Card Footer with Actions -->
    <div class="card-footer">
      <div class="card-actions">
        <button 
          @click="testService" 
          class="action-button test"
          :disabled="serviceStatus !== 'UP'"
        >
          Test
        </button>
        <button 
          @click="$emit('restart', service.id)" 
          class="action-button restart"
          :disabled="serviceStatus !== 'DOWN'"
        >
          Restart
        </button>
      </div>
      <div class="last-checked">
        Last checked: {{ formatTime(service.lastChecked) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSystemStore } from '@/stores/system'
import type { BackendService, ServiceHealth, ServiceMetrics, ServiceStatus } from '@/types'
import HealthStatusBadge from './HealthStatusBadge.vue'

interface Props {
  service: BackendService
  health?: ServiceHealth
  metrics?: ServiceMetrics
}

const props = defineProps<Props>()
const emit = defineEmits(['restart'])

const systemStore = useSystemStore()
const serviceStatus = computed(() => {
  const status = props.service.name ? 
    systemStore.services.find(s => s.name === props.service.name)?.status || 'PENDING' 
    : 'PENDING'
  return status as 'UP' | 'DOWN' | 'WARNING' | 'PENDING'
})

const statusClass = computed(() => {
  const status = serviceStatus.value
  return {
    'service-up': status === 'UP',
    'service-down': status === 'DOWN',
    'service-warning': status === 'WARNING',
    'service-pending': status === 'PENDING'
  }
})

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i]
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return `${Math.floor(seconds / 86400)}d`
}

function getMetricColor(value: number, type: 'cpu' | 'memory' | 'response'): string {
  switch (type) {
    case 'cpu':
      if (value < 30) return '#10b981'
      if (value < 70) return '#f59e0b'
      return '#ef4444'
    case 'memory':
      if (value < 60) return '#10b981'
      if (value < 85) return '#f59e0b'
      return '#ef4444'
    case 'response':
      if (value < 100) return '#10b981'
      if (value < 300) return '#f59e0b'
      return '#ef4444'
    default:
      return '#6b7280'
  }
}

function formatTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function testService() {
  window.open(props.service.endpoint, '_blank')
}
</script>

<style scoped>
.service-card {
  border-radius: 12px;
  padding: 1.25rem;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  background: white;
  cursor: pointer;
}

.service-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
}

.service-up {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
}

.service-down {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.service-warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
}

.service-pending {
  border-color: #6b7280;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.service-info {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.service-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 600;
}

.service-details {
  flex: 1;
}

.service-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 0.25rem 0;
}

.service-description {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.card-body {
  margin-bottom: 1rem;
}

.service-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.meta-value {
  font-size: 0.875rem;
  color: #1e293b;
  font-weight: 600;
}

.service-metrics {
  margin-bottom: 1rem;
}

.metric-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #64748b;
  width: 3.5rem;
}

.metric-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.metric-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
  width: 3rem;
  text-align: right;
}

.metric-bar {
  flex: 1;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  border-radius: 2px;
  transition: all 0.3s ease;
}

.service-error {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.error-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.error-message {
  font-size: 0.875rem;
  color: #dc2626;
  line-height: 1.4;
}

.service-endpoint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #64748b;
  background: #f8fafc;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.endpoint-label {
  font-weight: 500;
}

.endpoint-value {
  font-family: monospace;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.action-button {
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button.test {
  background: #f3f4f6;
  color: #374151;
}

.action-button.test:hover:not(:disabled) {
  background: #e5e7eb;
}

.action-button.restart {
  background: #ef4444;
  color: white;
  border-color: #dc2626;
}

.action-button.restart:hover:not(:disabled) {
  background: #dc2626;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.last-checked {
  font-size: 0.75rem;
  color: #64748b;
}

@media (max-width: 768px) {
  .service-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .card-footer {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
}
</style>