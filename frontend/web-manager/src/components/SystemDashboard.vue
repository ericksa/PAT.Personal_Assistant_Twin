<template>
  <div class="dashboard-container">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-left">
        <h1 class="dashboard-title">System Dashboard</h1>
        <p class="dashboard-subtitle">Monitor backend services and resources</p>
      </div>
      <div class="header-right">
        <HealthStatusBadge :status="overallHealth" show-label />
        <button 
          @click="refreshData" 
          :disabled="loading"
          class="refresh-button"
          :class="{ 'spinning': loading }"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
        <div class="last-updated">
          <span class="label">Last Updated:</span>
          <span>{{ formatTime(lastUpdated) }}</span>
        </div>
      </div>
    </header>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <SummaryCard
        v-for="card in summaryCards"
        :key="card.id"
        :title="card.title"
        :value="card.value"
        :icon="card.icon"
        :color="card.color"
        :trend="card.trend"
        :help-text="card.helpText"
      />
    </div>

    <!-- Services Grid -->
    <section class="services-section">
      <div class="section-header">
        <h2 class="section-title">Backend Services</h2>
        <ServiceFilters 
          v-model="selectedCategory" 
          :categories="categories"
        />
      </div>
      
      <div class="services-grid">
        <ServiceCard
          v-for="service in filteredServices"
          :key="service.id"
          :service="service"
          :health="serviceHealth[service.id]"
          :metrics="serviceMetrics[service.id]"
          @restart="restartService"
        />
      </div>
    </section>

    <!-- Resource Usage -->
    <section class="resources-section">
      <h2 class="section-title">Resource Usage</h2>
      <ResourceChart :resources="resources" :metrics="serviceMetrics" />
    </section>

    <!-- Loading and Error States -->
    <div v-if="loading && services.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>Loading system status...</p>
    </div>

    <div v-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Failed to load system status</h3>
      <p>{{ error }}</p>
      <button @click="refreshData" class="retry-button">Retry</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSystemStore } from '@/stores/system'
import HealthStatusBadge from './HealthStatusBadge.vue'
import ServiceCard from './ServiceCard.vue'
import ServiceFilters from './ServiceFilters.vue'
import SummaryCard from './SummaryCard.vue'
import ResourceChart from './ResourceChart.vue'

const systemStore = useSystemStore()
const {
  backendServices,
  services,
  serviceHealth,
  serviceMetrics,
  resources,
  lastUpdated,
  error,
  loading,
  overallHealth,
  activeServices,
  totalServices,
  avgResponseTime,
  totalMemoryUsage,
  totalCpuUsage
} = storeToRefs(systemStore)

const selectedCategory = ref<string>('all')

const categories = [
  { value: 'all', label: 'All Services', color: '#6b7280' },
  { value: 'core', label: 'Core', color: '#3b82f6' },
  { value: 'ingestion', label: 'Ingestion', color: '#10b981' },
  { value: 'processing', label: 'Processing', color: '#f59e0b' },
  { value: 'interface', label: 'Interface', color: '#8b5cf6' }
]

const filteredServices = computed(() => {
  if (selectedCategory.value === 'all') return backendServices.value
  return backendServices.value.filter(s => s.category === selectedCategory.value)
})

const summaryCards = computed(() => [
  {
    id: 'services',
    title: 'Active Services',
    value: `${activeServices.value}/${totalServices.value}`,
    icon: '🟢',
    color: '#10b981',
    trend: activeServices.value === totalServices.value ? 'up' : 'down',
    helpText: 'Number of healthy backend services'
  },
  {
    id: 'response-time',
    title: 'Avg Response Time',
    value: `${avgResponseTime.value}ms`,
    icon: '⏱️',
    color: avgResponseTime.value < 100 ? '#10b981' : avgResponseTime.value < 300 ? '#f59e0b' : '#ef4444',
    trend: avgResponseTime.value < 100 ? 'up' : 'down',
    helpText: 'Average service response time'
  },
  {
    id: 'memory',
    title: 'Memory Usage',
    value: `${totalMemoryUsage.value.toFixed(0)}MB`,
    icon: '🧠',
    color: totalMemoryUsage.value < 1024 ? '#10b981' : totalMemoryUsage.value < 2048 ? '#f59e0b' : '#ef4444',
    trend: 'stable',
    helpText: 'Total memory used by all services'
  },
  {
    id: 'cpu',
    title: 'CPU Usage',
    value: `${totalCpuUsage.value}%`,
    icon: '💻',
    color: totalCpuUsage.value < 30 ? '#10b981' : totalCpuUsage.value < 60 ? '#f59e0b' : '#ef4444',
    trend: totalCpuUsage.value < 50 ? 'up' : 'down',
    helpText: 'Total CPU usage across all services'
  }
])

async function refreshData() {
  await Promise.all([
    systemStore.checkServices(),
    systemStore.fetchResourceUsage()
  ])
}

function restartService(serviceId: string) {
  systemStore.restartService(serviceId)
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

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.header-left .dashboard-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background: #2563eb;
  transform: scale(1.02);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-button.spinning svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.last-updated {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 0.875rem;
  color: #64748b;
}

.last-updated .label {
  font-weight: 500;
  color: #475569;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.services-section {
  margin-bottom: 2rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.resources-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  text-align: center;
  background: white;
  border-radius: 12px;
  margin: 2rem 0;
}

.spinner {
  width: 2.5rem;
  height: 2.5rem;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-state .error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-state h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.error-state p {
  color: #64748b;
  margin-bottom: 1.5rem;
}

.retry-button {
  padding: 0.625rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-button:hover {
  background: #2563eb;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .services-grid {
    grid-template-columns: 1fr;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>