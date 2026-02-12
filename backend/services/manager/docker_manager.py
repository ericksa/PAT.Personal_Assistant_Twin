import subprocess
import json
import re
import os
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Union, cast
import logging
import asyncio

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self, compose_files: Optional[List[str]] = None):
        """Manages Docker containers for PAT services.

        Args:
            compose_files: List of docker-compose.yml files (defaults to ['docker-compose.yml'])
        """
        self.compose_files: List[str] = (
            compose_files if compose_files is not None else ["docker-compose.yml"]
        )
        self.compose_cmd = self._get_compose_command()
        self.cached_services = None

        logger.info(
            f"Initialized DockerManager with compose files: {self.compose_files}"
        )
        logger.info(f"Using compose command: {' '.join(self.compose_cmd)}")

    def _get_compose_command(self) -> List[str]:
        """Determine whether to use 'docker compose' or 'docker-compose'"""
        try:
            # Try docker compose first
            subprocess.run(
                ["docker", "compose", "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            return ["docker", "compose"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fall back to docker-compose
        try:
            subprocess.run(
                ["docker-compose", "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            return ["docker-compose"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        raise RuntimeError(
            "Neither 'docker compose' nor 'docker-compose' command found"
        )

    def _run_command(
        self, cmd: List[str], env: Optional[Dict[str, str]] = None, timeout: float = 60
    ) -> Tuple[bool, str, str]:
        """Run a shell command and return (success, stdout, stderr)"""
        try:
            # Join command if shell=True, but better to use list with shell=False
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=False,
                env=env,
                timeout=timeout,
            )
            return (
                result.returncode == 0,
                result.stdout.strip(),
                result.stderr.strip(),
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            return False, "", "command timed out"
        except Exception as e:
            logger.error(f"Command failed: {' '.join(cmd)}, error: {str(e)}")
            return False, "", str(e)

    def get_container_status(self, container_name: str) -> Tuple[str, Optional[str]]:
        """Get status of a Docker container.

        Returns:
            (status, container_id) tuple
            status: 'running', 'exited', 'not_found', or other Docker status
            container_id: Short container ID (first 12 chars) or None
        """
        success, stdout, stderr = self._run_command(
            [
                "docker",
                "inspect",
                "--format",
                "{{.State.Status}}|||{{.Id}}",
                container_name,
            ]
        )

        if not success:
            if "No such container" in stderr:
                return "not_found", None
            logger.error(f"Failed to inspect container {container_name}: {stderr}")
            return "error", None

        try:
            status, container_id = stdout.split("|||")
            return status, container_id[:12]  # Return short ID
        except Exception as e:
            logger.error(f"Failed to parse container status: {stdout}, error: {str(e)}")
            return "error", None

    def start_container(self, container_name: str) -> Tuple[bool, str]:
        """Start a Docker container"""
        logger.info(f"Starting container {container_name}")
        success, stdout, stderr = self._run_command(["docker", "start", container_name])

        if success:
            return True, f"Container {container_name} started"
        else:
            msg = f"Failed to start {container_name}: {stderr}"
            logger.error(msg)
            return False, msg

    def stop_container(
        self, container_name: str, timeout: int = 30
    ) -> Tuple[bool, str]:
        """Stop a Docker container"""
        logger.info(f"Stopping container {container_name}")
        success, stdout, stderr = self._run_command(
            ["docker", "stop", "--time", str(timeout), container_name]
        )

        if success:
            return True, f"Container {container_name} stopped"
        else:
            msg = f"Failed to stop {container_name}: {stderr}"
            logger.error(msg)
            return False, msg

    def restart_container(self, container_name: str) -> Tuple[bool, str]:
        """Restart a Docker container"""
        logger.info(f"Restarting container {container_name}")
        success, stdout, stderr = self._run_command(
            ["docker", "restart", container_name]
        )

        if success:
            return True, f"Container {container_name} restarted"
        else:
            msg = f"Failed to restart {container_name}: {stderr}"
            logger.error(msg)
            return False, msg

    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get logs from a container"""
        success, stdout, stderr = self._run_command(
            ["docker", "logs", "--tail", str(tail), "--timestamps", container_name]
        )

        if success:
            return stdout
        else:
            logger.error(f"Failed to get logs for {container_name}: {stderr}")
            return f"Error getting logs: {stderr}"

    def get_container_stats(
        self, container_name: str
    ) -> Dict[str, Union[float, int, str]]:
        """Get container stats (CPU%, memory usage, etc.)"""
        success, stdout, stderr = self._run_command(
            ["docker", "stats", "--no-stream", "--format", "json", container_name]
        )

        if not success or not stdout:
            logger.error(f"Failed to get stats for {container_name}: {stderr}")
            return {}

        try:
            # Get last line of output (most recent stats)
            lines = [line for line in stdout.split("\n") if line.strip()]
            if not lines:
                return {}

            stats = json.loads(lines[-1])

            # Parse relevant stats
            return {
                "cpu_percent": float(stats["CPUPerc"].rstrip("%"))
                if stats.get("CPUPerc")
                else 0.0,
                "memory_usage": self._parse_docker_memory(stats.get("MemUsage", "")),
                "network_io": stats.get("NetIO", "N/A"),
                "block_io": stats.get("BlockIO", "N/A"),
                "pids": int(stats.get("PIDs", 0)),
            }

        except Exception as e:
            logger.error(f"Failed to parse stats: {stdout}, error: {str(e)}")
            return {}

    def _parse_docker_memory(self, memory_str: str) -> int:
        """Parse Docker memory string like '1.5GiB / 15.6GiB' into bytes"""
        try:
            # Extract first part (usage)
            usage_part = memory_str.split()[0]

            # Parse size with units (KB, MB, GB)
            if usage_part.endswith("GiB"):
                return int(float(usage_part.replace("GiB", "")) * 1024 * 1024 * 1024)
            elif usage_part.endswith("MiB"):
                return int(float(usage_part.replace("MiB", "")) * 1024 * 1024)
            elif usage_part.endswith("KiB"):
                return int(float(usage_part.replace("KiB", "")) * 1024)
            else:
                return int(float(usage_part))
        except (ValueError, IndexError, AttributeError):
            return 0

    async def stream_container_logs(
        self, container_name: str
    ) -> AsyncGenerator[str, None]:
        """Stream container logs in real-time"""
        cmd = f"docker logs --tail 0 --follow {container_name}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            limit=1024 * 1024,  # 1MB buffer
        )

        # Type hint for stdout since we know it's set
        stdout = cast(asyncio.StreamReader, process.stdout)

        try:
            while True:
                # Read a line (with timeout to prevent hanging during shutdown)
                try:
                    line = await asyncio.wait_for(stdout.readline(), timeout=10.0)
                except asyncio.TimeoutError:
                    if process.returncode is not None:
                        break
                    continue

                if not line:
                    if process.returncode is not None:
                        break
                    await asyncio.sleep(0.1)
                    continue

                yield line.decode("utf-8", errors="replace").rstrip("\n")
        except asyncio.CancelledError:
            logger.info("Log streaming cancelled")
            # If the process is still running, send the interrupt signal to exit quickly
            if process.returncode is None:
                process.terminate()
        finally:
            if process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Error cleaning up log process: {str(e)}")

    def stop_all_containers(self) -> Dict[str, Dict[str, str]]:
        """Stop all Docker containers managed by docker-compose"""
        logger.info("Stopping all Docker containers")
        cmd = self.compose_cmd + self._compose_files_args() + ["stop"]
        success, stdout, stderr = self._run_command(
            cmd, timeout=300
        )  # 5 minute timeout

        results = {}
        if not success:
            logger.error(f"Failed to stop all containers: {stderr}")
            return results

        logger.info(f"Successfully stopped containers: {stdout}")

        # Parse compose output to get stopped services
        # This is somewhat fragile but docker-compose doesn't have a better output format
        service_names = [
            os.path.basename(path).replace(".yml", "").replace("docker-compose-", "")
            for path in self.compose_files
        ]

        for line in stdout.split("\n"):
            for service in service_names:
                if f"Stopping {service}" in line or f"Stopped {service}" in line:
                    results[service] = {
                        "success": "done" in line.lower() or "stopped" in line.lower(),
                        "message": line.strip(),
                    }

        return results

    def _compose_files_args(self) -> List[str]:
        """Build the compose file arguments"""
        args = []
        for f in self.compose_files:
            args.extend(["-f", f])
        return args
