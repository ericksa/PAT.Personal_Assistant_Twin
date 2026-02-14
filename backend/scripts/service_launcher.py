#!/usr/bin/env python3
"""
PAT Service Launcher with Process Management, Resource Monitoring & Resource Limiting
"""

import asyncio
import logging
import os
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import psutil
import setproctitle

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a service"""

    name: str
    script_path: str
    port: int
    health_url: str
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    timeout_seconds: int = 30
    restart_on_failure: bool = True
    max_restarts: int = 3
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceStatus:
    """Status tracking for a service"""

    name: str
    process: Optional[asyncio.subprocess.Process] = None
    status: str = "stopped"  # stopped, starting, running, error, restarting
    restarts: int = 0
    last_start_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    health_url: str = ""
    port: int = 0
    pid: Optional[int] = None


class ResourceMonitor:
    """Monitor and limit system resources for services"""

    def __init__(self):
        self.monitored_processes: Dict[str, psutil.Process] = {}
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor")

    def add_process(self, service_name: str, pid: int):
        """Add a process to monitor"""
        try:
            process = psutil.Process(pid)
            self.monitored_processes[service_name] = process
            self.logger.info(f"Added {service_name} (PID: {pid}) to monitoring")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Failed to monitor {service_name} (PID: {pid}): {e}")

    def remove_process(self, service_name: str):
        """Remove a process from monitoring"""
        if service_name in self.monitored_processes:
            del self.monitored_processes[service_name]
            self.logger.info(f"Removed {service_name} from monitoring")

    def get_process_stats(self, service_name: str) -> Dict[str, float]:
        """Get resource usage stats for a service"""
        if service_name not in self.monitored_processes:
            return {}

        try:
            process = self.monitored_processes[service_name]
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.remove_process(service_name)
            return {}

    def check_resource_limits(
        self, service_name: str, max_memory_mb: int, max_cpu_percent: int
    ) -> bool:
        """Check if service is within resource limits"""
        stats = self.get_process_stats(service_name)

        if not stats:
            return False

        memory_ok = stats["memory_mb"] <= max_memory_mb
        cpu_ok = stats["cpu_percent"] <= max_cpu_percent

        if not memory_ok:
            self.logger.warning(
                f"{service_name} memory usage ({stats['memory_mb']:.1f}MB) exceeds limit ({max_memory_mb}MB)"
            )

        if not cpu_ok:
            self.logger.warning(
                f"{service_name} CPU usage ({stats['cpu_percent']:.1f}%) exceeds limit ({max_cpu_percent}%)"
            )

        return memory_ok and cpu_ok

    async def monitor_loop(self, service_configs: Dict[str, ServiceConfig]):
        """Main monitoring loop"""
        self.logger.info("Starting resource monitoring")

        while True:
            try:
                for service_name, config in service_configs.items():
                    if service_name in self.monitored_processes:
                        # Check resource limits
                        within_limits = self.check_resource_limits(
                            service_name, config.max_memory_mb, config.max_cpu_percent
                        )

                        # Get current stats for logging
                        stats = self.get_process_stats(service_name)
                        if stats:
                            self.logger.debug(
                                f"{service_name}: {stats['memory_mb']:.1f}MB, {stats['cpu_percent']:.1f}% CPU"
                            )

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(5)


class PATServiceLauncher:
    """Enhanced PAT Service Launcher with monitoring and resource management"""

    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.status: Dict[str, ServiceStatus] = {}
        self.resource_monitor = ResourceMonitor()
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.ServiceLauncher")

    def register_service(self, config: ServiceConfig):
        """Register a service for management"""
        self.services[config.name] = config
        self.status[config.name] = ServiceStatus(
            name=config.name, health_url=config.health_url, port=config.port
        )
        self.logger.info(f"Registered service: {config.name} on port {config.port}")

    async def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        if service_name not in self.services:
            self.logger.error(f"Service {service_name} not registered")
            return False

        config = self.services[service_name]
        status = self.status[service_name]

        # Set process title for Activity Monitor
        setproctitle.setproctitle(f"PAT-{service_name.replace('-', '_').upper()}")

        self.logger.info(f"Starting {service_name}...")
        status.status = "starting"

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.environment)

            # Start the service
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                config.script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=Path(config.script_path).parent,
            )

            status.process = process
            status.pid = process.pid
            status.last_start_time = time.time()
            status.status = "running"

            # Add to resource monitoring
            self.resource_monitor.add_process(service_name, process.pid)

            self.logger.info(f"Started {service_name} (PID: {process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start {service_name}: {e}")
            status.status = "error"
            return False

    async def stop_service(self, service_name: str):
        """Stop a single service"""
        if service_name not in self.status:
            return

        status = self.status[service_name]

        if status.process:
            self.logger.info(f"Stopping {service_name}...")
            try:
                status.process.terminate()
                try:
                    await asyncio.wait_for(status.process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    self.logger.warning(f"Force killing {service_name}...")
                    status.process.kill()
                    await status.process.wait()
            except Exception as e:
                self.logger.error(f"Error stopping {service_name}: {e}")
            finally:
                status.process = None
                status.pid = None
                status.status = "stopped"

        # Remove from resource monitoring
        self.resource_monitor.remove_process(service_name)
        self.logger.info(f"Stopped {service_name}")

    async def restart_service(self, service_name: str):
        """Restart a service"""
        config = self.services[service_name]
        status = self.status[service_name]

        if status.restarts >= config.max_restarts:
            self.logger.error(f"Max restarts reached for {service_name}")
            status.status = "error"
            return

        status.restarts += 1
        status.status = "restarting"

        await self.stop_service(service_name)
        await asyncio.sleep(2)  # Brief pause before restart
        await self.start_service(service_name)

    async def start_all_services(self):
        """Start all registered services"""
        self.running = True
        self.logger.info("Starting all PAT services...")

        # Start services sequentially to avoid overwhelming the system
        for service_name in self.services.keys():
            if self.running:
                success = await self.start_service(service_name)
                if success:
                    await asyncio.sleep(2)  # Wait between starts
                else:
                    self.logger.error(f"Failed to start {service_name}")

    async def stop_all_services(self):
        """Stop all services"""
        self.running = False
        self.logger.info("Stopping all PAT services...")

        # Stop all services in parallel
        stop_tasks = [self.stop_service(name) for name in self.services.keys()]
        await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def health_check_loop(self):
        """Monitor service health and restart failed services"""
        self.logger.info("Starting health monitoring")

        while self.running:
            try:
                for service_name in self.services.keys():
                    if not self.running:
                        break

                    status = self.status[service_name]
                    config = self.services[service_name]

                    # Skip if service is not running
                    if status.status != "running" or not status.process:
                        continue

                    # Check if process is still alive
                    if status.process.returncode is not None:
                        self.logger.warning(
                            f"{service_name} process has exited, restarting..."
                        )
                        await self.restart_service(service_name)
                        continue

                    # Perform HTTP health check
                    try:
                        import httpx

                        async with httpx.AsyncClient(timeout=10) as client:
                            response = await client.get(config.health_url)
                            if response.status_code >= 400:
                                self.logger.warning(
                                    f"{service_name} health check failed: {response.status_code}"
                                )

                                if config.restart_on_failure:
                                    await self.restart_service(service_name)
                    except Exception as e:
                        self.logger.warning(
                            f"Health check failed for {service_name}: {e}"
                        )
                        if config.restart_on_failure:
                            await self.restart_service(service_name)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(10)

    def get_status_summary(self) -> Dict:
        """Get overall status summary"""
        total_services = len(self.services)
        running_services = sum(
            1 for status in self.status.values() if status.status == "running"
        )

        # Get resource stats for running services
        resource_stats = {}
        for service_name, status in self.status.items():
            if status.status == "running":
                stats = self.resource_monitor.get_process_stats(service_name)
                if stats:
                    resource_stats[service_name] = stats

        return {
            "total_services": total_services,
            "running_services": running_services,
            "services": {
                name: {
                    "status": status.status,
                    "pid": status.pid,
                    "restarts": status.restarts,
                    "resources": self.resource_monitor.get_process_stats(name),
                }
                for name, status in self.status.items()
            },
            "resource_stats": resource_stats,
        }


def create_service_configs() -> Dict[str, ServiceConfig]:
    """Create service configurations"""
    backend_path = Path(__file__).parent.parent.absolute()

    configs = {
        "ingest": ServiceConfig(
            name="ingest",
            script_path=str(backend_path / "services" / "ingest" / "app.py"),
            port=8001,
            health_url="http://localhost:8001/health",
            max_memory_mb=512,
            max_cpu_percent=80,
            environment={"PORT": "8001", "LOG_LEVEL": "INFO"},
        ),
        "agent": ServiceConfig(
            name="agent",
            script_path=str(backend_path / "services" / "agent" / "app.py"),
            port=8002,
            health_url="http://localhost:8002/health",
            max_memory_mb=512,
            max_cpu_percent=80,
            environment={"PORT": "8002", "LOG_LEVEL": "INFO"},
        ),
        "pat-core": ServiceConfig(
            name="pat-core",
            script_path=str(backend_path / "src" / "main_pat.py"),
            port=8010,
            health_url="http://localhost:8010/pat/health",
            max_memory_mb=1024,
            max_cpu_percent=80,
            environment={"PAT_PORT": "8010", "LOG_LEVEL": "INFO"},
        ),
        "mcp": ServiceConfig(
            name="mcp",
            script_path=str(backend_path / "services" / "mcp" / "app.py"),
            port=8003,
            health_url="http://localhost:8003/health",
            max_memory_mb=256,
            max_cpu_percent=60,
            environment={"PORT": "8003", "LOG_LEVEL": "INFO"},
        ),
        "manager": ServiceConfig(
            name="manager",
            script_path=str(backend_path / "services" / "manager" / "app.py"),
            port=8888,
            health_url="http://localhost:8888/api/services",
            max_memory_mb=256,
            max_cpu_percent=50,
            environment={"PORT": "8888", "LOG_LEVEL": "INFO"},
        ),
    }

    return configs


async def main():
    """Main launcher function"""
    print("🚀 PAT Service Launcher")
    print("=" * 50)

    # Set main process title
    setproctitle.setproctitle("PAT-SERVICE-LAUNCHER")

    launcher = PATServiceLauncher()

    # Register services
    for name, config in create_service_configs().items():
        launcher.register_service(config)

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        launcher.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    monitor_task = None
    health_task = None

    try:
        # Start all services
        await launcher.start_all_services()

        # Start resource monitoring in background
        monitor_task = asyncio.create_task(
            launcher.resource_monitor.monitor_loop(create_service_configs())
        )

        # Start health monitoring
        health_task = asyncio.create_task(launcher.health_check_loop())

        # Main monitoring loop
        print("\n" + "=" * 50)
        print("✅ All services started successfully!")
        print("📊 Resource monitoring and health checks active")
        print("Press Ctrl+C to stop all services")
        print("=" * 50)

        # Periodic status reporting
        while launcher.running:
            await asyncio.sleep(60)  # Report every minute

            status = launcher.get_status_summary()
            print(f"\n[{time.strftime('%H:%M:%S')}] Status Summary:")
            print(
                f"  Running: {status['running_services']}/{status['total_services']} services"
            )

            for name, info in status["services"].items():
                resources = info.get("resources", {})
                memory = resources.get("memory_mb", 0)
                cpu = resources.get("cpu_percent", 0)
                print(
                    f"  • {name}: {info['status']} (PID: {info['pid']}, {memory:.1f}MB, {cpu:.1f}% CPU)"
                )

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Launcher error: {e}")
    finally:
        launcher.running = False
        await launcher.stop_all_services()

        # Cancel background tasks if they exist
        if monitor_task:
            monitor_task.cancel()
        if health_task:
            health_task.cancel()

        print("✅ All services stopped")


if __name__ == "__main__":
    asyncio.run(main())
