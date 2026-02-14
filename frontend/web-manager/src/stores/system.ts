import { defineStore } from 'pinia'
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import type { 
  ServiceStatus, 
  ResourceUsage, 
  BackendService, 
  ServiceHealth, 
  ServiceMetrics 
} from '@/types'

export const useSystemStore = defineStore('system', () => {
  // PAT Backend Services Configuration
  const backendServices = ref<BackendService[]>([
    {
      id: 'ingest',
      name: 'ingest',
      displayName: 'Ingest Service',
      description: 'Data ingestion and processing pipeline',
      endpoint: 'http://localhost:8101',
      healthEndpoint: 'http://localhost:8101/health',
      metricsEndpoint: 'http://localhost:8101/metrics',
      category: 'ingestion',
      icon: '📥',
      color: '#10b981'
    },
    {
      id: 'agent',
      name: 'agent',
      displayName: 'Agent Service',
      description: 'AI agent orchestration and task management',
      endpoint: 'http://localhost:8201',
      healthEndpoint: 'http://localhost:8201/health',
      metricsEndpoint: 'http://localhost:8201/metrics',
      category: 'core',
      icon: '🤖',
      color: '#3b82f6'
    },
    {
      id: 'core',
      name: 'core',
      displayName: 'Core Service',
      description: 'Central API and business logic',
      endpoint: 'http://localhost:8301',
      healthEndpoint: 'http://localhost:8301/health',
      metricsEndpoint: 'http://localhost:8301/metrics',
      category: 'core',
      icon: '⚡',
      color: '#f59e0b'
    },
    {
      id: 'mcp',
      name: 'mcp',
      displayName: 'MCP Service',
      description: 'Model Context Protocol and LLM integration',
      endpoint: 'http://localhost:8401',
      healthEndpoint: 'http://localhost:8401/health',
      metricsEndpoint: 'http://localhost:8401/metrics',
      category: 'interface',
      icon: '🧠',
      color: '#8b5cf6'
    },
    {
      id: 'manager',
      name: 'manager',
      displayName: 'Manager Service',
      description: 'System management and monitoring',
      endpoint: 'http://localhost:8501',
      healthEndpoint: 'http://localhost:8501/health',
      metricsEndpoint: 'http://localhost:8501/metrics',
      category: 'interface',
      icon: '🎛️',
      color: '#ef4444'
    },
    {
      id: 'bff',
      name: 'bff',
      displayName: 'BFF Service',
      description: 'Backend-for-Frontend API gateway',
      endpoint: 'http://localhost:8888',
      healthEndpoint: 'http://localhost:8888/health',
      metricsEndpoint: 'http://localhost:8888/metrics',
      category: 'interface',
      icon: '🚪',
      color: '#06b6d4'
    }
  ])

  // Service status data
  const services = ref<ServiceStatus[]>([])
  const serviceHealth = reactive<Record<string, ServiceHealth>>({})
  const serviceMetrics = reactive<Record<string, ServiceMetrics>>({})
  
  const resources = ref<ResourceUsage>({
    cpu: 0,
    memory: 0,
    disk: 0,
    timestamp: new Date(),
    processes: []
  })
  
  const lastUpdated = ref<Date>(new Date())
  const error = ref<string | null>(null)
  const loading = ref<boolean>(false)
  
  // Computed properties
  const overallHealth = computed(() => {
    const statuses = services.value.map(s => s.status)
    if (statuses.some(s => s === 'DOWN')) return 'DOWN'
    if (statuses.some(s => s === 'WARNING')) return 'WARNING'
    if (statuses.every(s => s === 'UP')) return 'UP'
    return 'PENDING'
  })
  
  const isHealthy = computed(() => overallHealth.value === 'UP')
  const hasIssues = computed(() => overallHealth.value === 'DOWN' || overallHealth.value === 'WARNING')
  
  const activeServices = computed(() => 
    services.value.filter(s => s.status === 'UP').length
  )
  
  const totalServices = computed(() => backendServices.value.length)
  
  const avgResponseTime = computed(() => {
    const responseTimes = services.value
      .filter(s => s.responseTime)
      .map(s => s.responseTime) as number[]
    
    if (responseTimes.length === 0) return 0
    return Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
  })

  const totalMemoryUsage = computed(() => {
    const metrics = Object.values(serviceMetrics)
    if (metrics.length === 0) return 0
    return metrics.reduce((sum, m) => sum + (m.memory_used_mb || 0), 0)
  })

  const totalCpuUsage = computed(() => {
    const metrics = Object.values(serviceMetrics)
    if (metrics.length === 0) return 0
    return Math.round(metrics.reduce((sum, m) => sum + (m.cpu_usage || 0), 0))
  })

  // Helper functions
  function formatUptime(seconds: number): string {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
    return `${Math.floor(seconds / 86400)}d`
  }

  function healthStatusToDisplayStatus(health: string): 'UP' | 'DOWN' | 'WARNING' | 'PENDING' {
    switch (health) {
      case 'healthy': return 'UP'
      case 'unhealthy': return 'DOWN'
      case 'degraded': return 'WARNING'
      default: return 'PENDING'
    }
  }

  // Main API functions
  async function checkServices() {
    loading.value = true
    error.value = null
    
    try {
      // Update status for each backend service
      await Promise.all(
        backendServices.value.map(async (service) => {
          try {
            const startTime = Date.now()
            const healthResponse = await fetch(service.healthEndpoint, {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' }
            })
            const responseTime = Date.now() - startTime
            
            if (healthResponse.ok) {
              const healthData = await healthResponse.json()
              serviceHealth[service.id] = healthData
              
              // Update service status
              services.value = services.value.filter(s => s.name !== service.name)
              services.value.push({
                name: service.name,
                status: healthStatusToDisplayStatus(healthData.status),
                message: healthData.status || 'Unknown',
                version: healthData.version,
                uptime: healthData.uptime ? formatUptime(healthData.uptime) : undefined,
                endpoint: service.endpoint,
                responseTime,
                lastChecked: new Date()
              })
              
              // Fetch metrics if available
              if (service.metricsEndpoint) {
                await fetchMetrics(service)
              }
            } else {
              services.value = services.value.filter(s => s.name !== service.name)
              services.value.push({
                name: service.name,
                status: 'DOWN',
                message: `HTTP ${healthResponse.status}`,
                endpoint: service.endpoint,
                responseTime,
                lastChecked: new Date()
              })
            }
          } catch (e) {
            services.value = services.value.filter(s => s.name !== service.name)
            services.value.push({
              name: service.name,
              status: 'DOWN',
              message: e instanceof Error ? e.message : 'Connection failed',
              endpoint: service.endpoint,
              error: e instanceof Error ? e.message : 'Connection failed',
              lastChecked: new Date()
            })
          }
        })
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to check services'
      console.error('Service check error:', e)
    } finally {
      lastUpdated.value = new Date()
      loading.value = false
    }
  }
  
  async function fetchMetrics(service: BackendService) {
    try {
      const metricsResponse = await fetch(service.metricsEndpoint, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json()
        serviceMetrics[service.id] = metricsData
      }
    } catch (e) {
      console.warn(`Failed to fetch metrics for ${service.name}:`, e)
    }
  }
  
  async function fetchResourceUsage() {
    try {
      const response = await fetch('http://localhost:8888/metrics', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (!response.ok) return
      
      const data = await response.json()
      resources.value = {
        cpu: data.system?.cpu_percent || 0,
        memory: data.system?.memory_percent || 0,
        disk: data.system?.disk_percent || 0,
        timestamp: new Date(data.timestamp || Date.now()),
        processes: data.processes || []
      }
      lastUpdated.value = new Date()
    } catch (e) {
      console.error('Failed to fetch resource usage:', e)
    }
  }

  async function restartService(serviceId: string) {
    const service = backendServices.value.find(s => s.id === serviceId)
    if (!service) throw new Error(`Service ${serviceId} not found`)
    
    try {
      const response = await fetch(`${service.endpoint}/restart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (!response.ok) {
        throw new Error(`Failed to restart service: HTTP ${response.status}`)
      }
      
      // Refresh service status
      await checkServices()
      return true
    } catch (e) {
      console.error(`Failed to restart service ${serviceId}:`, e)
      throw e
    }
  }
  
  // Auto-check services on mount
  onMounted(() => {
    checkServices()
    fetchResourceUsage()
    
    // Set up interval for auto-refresh (every 30 seconds)
    const interval = setInterval(async () => {
      await checkServices()
      await fetchResourceUsage()
    }, 30000)
    
    onUnmounted(() => {
      clearInterval(interval)
    })
  })
  
  return {
    backendServices,
    services,
    serviceHealth,
    serviceMetrics,
    resources,
    lastUpdated,
    error,
    loading,
    overallHealth,
    isHealthy,
    hasIssues,
    activeServices,
    totalServices,
    avgResponseTime,
    totalMemoryUsage,
    totalCpuUsage,
    checkServices,
    fetchResourceUsage,
    restartService,
    formatUptime
  }
})