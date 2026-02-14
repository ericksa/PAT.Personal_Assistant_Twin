<template>
  <div>
    <div class="resource-charts">
      <div class="chart-card">
        <h3 class="chart-title">📊 System Resources</h3>
        <div class="chart-grid">
          <div class="resource-item">CPU</div>
          <div class="progress-bar">
            <div
              class="progress-fill cpu"
              :style="{ width: `${resources.cpu}%` }"
            ></div>
          </div>
          <div class="resource-value">{{ Math.round(resources.cpu) }}%</div>

          <div class="resource-item">Memory</div>
          <div class="progress-bar">
            <div
              class="progress-fill memory"
              :style="{ width: `${resources.memory}%` }"
            ></div>
          </div>
          <div class="resource-value">{{ Math.round(resources.memory) }}%</div>

          <div class="resource-item">Disk</div>
          <div class="progress-bar">
            <div
              class="progress-fill disk"
              :style="{ width: `${resources.disk}%` }"
            ></div>
          </div>
          <div class="resource-value">{{ Math.round(resources.disk) }}%</div>
        </div>
      </div>

      <div class="metrics-chart">
        <h3 class="chart-title">📈 Service Metrics</h3>
        <div class="metrics-grid">
          <div
            v-for="(metric, serviceId) in formattedMetrics"
            :key="serviceId"
            class="metric-row"
          >
            <div class="service-name">{{ metric.name }}</div>
            <div class="metric-bars">
              <div class="metric-bar-group">
                <div class="metric-label">CPU</div>
                <div class="mini-bar">
                  <div
                    class="mini-fill"
                    :style="{
                      width: `${metric.cpu}%`,
                      backgroundColor: getMetricColor(metric.cpu, 'cpu')
                    }"
                  ></div>
                </div>
              </div>
              <div class="metric-bar-group">
                <div class="metric-label">Mem</div>
                <div class="mini-bar">
                  <div
                    class="mini-fill"
                    :style="{
                      width: `${metric.memory}%`,
                      backgroundColor: getMetricColor(metric.memory, 'memory')
                    }`
                  ></div>
                </div>
              </div>
            </div>
            <div class="metric-values">{{ metric.cpu }}% / {{ metric.memory }}%</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-footer">
      <div class="resource-timestamp">
        Last updated: {{ formatTime(resources.timestamp || new Date()) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ResourceUsage, ServiceMetrics } from '@/types'

interface Props {
  resources: ResourceUsage
  metrics: Record<string, ServiceMetrics>
}

const props = defineProps<Props>()

const formattedMetrics = computed(() => {
  return Object.entries(props.metrics).map(([id, metric]) => {
    const services = {
      ingest: 'Ingest',
      agent: 'Agent', 
      core: 'Core',
      mcp: 'MCP',
      manager: 'Manager',
      bff: 'BFF'
    }
    
    return {
      id,
      name: services[id] || id,
      cpu: Math.round(metric.cpu_usage),
      memory: Math.round(metric.memory_usage)
    }
  })
})

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
</script>

<style scoped>
.resource-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.chart-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
}

.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 1rem 0;
}

.chart-grid {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.75rem;
  align-items: center;
}

.resource-item {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  width: 4rem;
}

.progress-bar {
  height: 0.75rem;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: all 0.5s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

.progress-fill.cpu {
  background: linear-gradient(90deg, #10b981, #059669);
}

.progress-fill.memory {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.progress-fill.disk {
  background: linear-gradient(90deg, #8b5cf6, #7c3aed);
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.resource-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: #1e293b;
  width: 3rem;
  text-align: right;
}

.metrics-chart {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.625rem;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
  background: #f8fafc;
}

.service-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  width: 3.5rem;
}

.metric-bars {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.metric-bar-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metric-label {
  font-size: 0.625rem;
  color: #64748b;
  font-weight: 500;
  width: 1.5rem;
}

.mini-bar {
  flex: 1;
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: all 0.5s ease;
}

.metric-values {
  font-size: 0.75rem;
  font-weight: 600;
  color: #1e293b;
  font-family: monospace;
  width: 5rem;
  text-align: right;
}

.chart-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-top: 0.75rem;
}

.resource-timestamp {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

@media (max-width: 768px) {
  .resource-charts {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
</style>