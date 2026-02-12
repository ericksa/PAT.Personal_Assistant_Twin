"""Manages Python processes for PAT services"""

import subprocess
import os
import asyncio
from typing import AsyncGenerator, Dict, Optional, List, Tuple
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PythonProcessManager:
    def __init__(self, backend_path: str, python_path: str):
        """
        Manages Python processes for PAT services.

        Args:
            backend_path (str): Root path of the backend repository
            python_path (str): Path to the Python interpreter to use
        """
        self.backend_path = str(Path(backend_path).absolute())
        self.python_path = python_path
        self.processes: Dict[str, subprocess.Popen[str]] = {}
        self.service_logs: Dict[str, List[str]] = {}

        logger.info(
            f"Initialized PythonProcessManager with backend_path={self.backend_path}"
        )
        logger.info(f"Using Python at: {self.python_path}")

    def start_service(
        self, service_id: str, script: str, env_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Optional[int]]:
        """Start a Python service

        Args:
            service_id: Unique ID for the service
            script: Relative path to the Python script (from backend_path)
            env_vars: Additional environment variables

        Returns:
            (success, message, pid)
        """
        # Set default env_vars if None
        if env_vars is None:
            env_vars = {}

        logger.info(f"Starting service {service_id} with script {script}")

        # Check if already running
        if service_id in self.processes and self.processes[service_id].poll() is None:
            msg = f"Service {service_id} is already running"
            logger.warning(msg)
            return False, msg, None

        # Prepare environment
        env = os.environ.copy()
        env.update({"PYTHONPATH": self.backend_path, "PYTHONUNBUFFERED": "1"})
        if env_vars:
            env.update(env_vars)

        # Build the command
        script_path = str(Path(self.backend_path) / script)
        cmd = [self.python_path, script_path]

        # Check script exists
        if not Path(script_path).exists():
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg)
            return False, error_msg, None

        logger.debug(f"Starting process: {' '.join(cmd)}")
        logger.debug(f"Working directory: {self.backend_path}")

        # Initialize logs list
        self.service_logs[service_id] = []

        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                cwd=self.backend_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Check that stdout was captured
            if process.stdout is None:
                raise RuntimeError("Failed to capture stdout for process")

            # Start background task to capture logs
            self._start_log_capture(service_id, process)

            self.processes[service_id] = process
            pid = process.pid

            logger.info(f"Started service {service_id} with PID {pid}")
            return True, f"Service {service_id} started", pid

        except Exception as e:
            error_msg = f"Failed to start service {service_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg, None

    def _start_log_capture(self, service_id: str, process: "subprocess.Popen[str]"):
        """Start capturing logs in a background thread"""
        import threading

        def capture():
            try:
                # Ensure stdout is available
                if process.stdout is None:
                    logger.error(f"No stdout for service {service_id}")
                    return

                # Read line by line
                for line in process.stdout:
                    if not line:
                        break
                    # Store log line with timestamp
                    timestamp = (
                        datetime.now().astimezone().isoformat(timespec="milliseconds")
                    )
                    log_line = f"[{timestamp}] {line.strip()}"
                    self.service_logs[service_id].append(log_line)

                    # Keep only the last 1000 lines of logs
                    if len(self.service_logs[service_id]) > 1000:
                        self.service_logs[service_id].pop(0)
            except Exception as e:
                logger.error(
                    f"Log capture error for {service_id}: {str(e)}", exc_info=True
                )

        log_thread = threading.Thread(target=capture, daemon=True)
        log_thread.start()

    def stop_service(self, service_id: str, timeout: int = 10) -> Tuple[bool, str]:
        """Stop a Python service

        Args:
            service_id: ID of the service to stop
            timeout: Seconds to wait before force killing

        Returns:
            (success, message)
        """
        logger.info(f"Stopping service {service_id}")

        if service_id not in self.processes:
            msg = f"Service {service_id} is not running"
            logger.warning(msg)
            return False, msg

        process = self.processes[service_id]

        try:
            # Try graceful termination first
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                logger.warning(
                    f"Service {service_id} not terminating, sending kill signal"
                )
                process.kill()
                process.wait()

            del self.processes[service_id]
            if service_id in self.service_logs:
                del self.service_logs[service_id]

            logger.info(f"Successfully stopped service {service_id}")
            return True, f"Stopped service {service_id}"

        except Exception as e:
            error_msg = f"Failed to stop service {service_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def get_status(self, service_id: str) -> Tuple[bool, Optional[int]]:
        """Check if service is running and get PID"""
        # 1. Check if we managed it in this session
        if service_id in self.processes:
            process = self.processes[service_id]
            if process.poll() is None:  # Still running
                return True, process.pid
            # Process has terminated
            del self.processes[service_id]

        # 2. Check if it's running elsewhere on the system (e.g. manually started)
        try:
            # Look for processes matching the service script name
            # We match 'main_pat.py' for 'core' for example
            from config import PYTHON_SERVICES

            service_config = PYTHON_SERVICES.get(service_id)
            if service_config and service_config.get("script"):
                script_name = service_config["script"].split("/")[-1]
                # Try pgrep -f first
                cmd = ["pgrep", "-f", script_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split("\n")
                    return True, int(pids[0])

                # Fallback: manually check port if available
                port = service_config.get("port")
                if port:
                    import socket

                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        if s.connect_ex(("localhost", port)) == 0:
                            return True, None  # Port is active, but PID unknown
        except Exception as e:
            logger.debug(f"System status check failed for {service_id}: {e}")

        return False, None

    def get_logs(self, service_id: str, tail: int = 100) -> List[str]:
        """Get logs for a service"""
        if service_id in self.service_logs:
            return self.service_logs[service_id][-tail:]
        return []

    async def stream_logs(self, service_id: str) -> AsyncGenerator[str, None]:
        """Stream logs from a running service"""
        if service_id not in self.service_logs:
            logger.warning(f"No logs for service {service_id}")
            return

        # For Python services, we'll monitor the service's logs queue
        queue = self.service_logs[service_id]

        # Start reading from the end
        start_index = len(queue)

        while True:
            # Check if service is still running
            running, _ = self.get_status(service_id)
            if not running:
                yield f"[INFO] Service {service_id} stopped"
                break

            # Check for new logs
            current_length = len(self.service_logs[service_id])
            if current_length > start_index:
                for i in range(start_index, current_length):
                    yield self.service_logs[service_id][i]
                start_index = current_length

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

    def get_all_logs(self, tail: int = 100) -> Dict[str, List[str]]:
        """Get logs for all services"""
        return {
            service_id: self.get_logs(service_id, tail)
            for service_id in list(self.service_logs.keys())
        }

    def stop_all_services(self) -> Dict[str, Dict[str, str]]:
        """Stop all managed services"""
        logger.info("Stopping all Python services")
        results = {}
        for service_id in list(self.processes.keys()):
            success, message = self.stop_service(service_id)
            results[service_id] = {"success": success, "message": message}
        return results

    def cleanup(self):
        """Clean up resources (stop all services)"""
        self.stop_all_services()
        logger.info("PythonProcessManager clean up complete")
