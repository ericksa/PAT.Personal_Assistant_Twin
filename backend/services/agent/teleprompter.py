# services/agent/teleprompter.py
import httpx
import asyncio
from config import logger

class TeleprompterManager:
    """Manages communication with the teleprompter service"""
    def __init__(self):
        self.teleprompter_url = "http://teleprompter-app:8000"
        self.timeout = 30

    async def broadcast_to_teleprompter(self, message: str) -> bool:
        """Send text to teleprompter via WebSocket broadcast"""
        try:
            async with httpx.AsyncClient() as client:
                # Health check first
                health_response = await client.get(f"{self.teleprompter_url}/health", timeout=5)
                if health_response.status_code != 200:
                    logger.warning(f"Teleprompter health check failed: {health_response.status_code}")
                    return False

                # Try to send message via WebSocket proxy endpoint (would need to be implemented)
                # For now, let's create a simple broadcast mechanism
                logger.info(f"Broadcasting to teleprompter: {message[:100]}...")
                # The actual WebSocket broadcast happens in the teleprompter service
                # We communicate via standard HTTP or create a WebSocket client
                
                # For MVP: Assume teleprompter has a broadcast endpoint
                broadcast_response = await client.post(
                    f"{self.teleprompter_url}/broadcast",
                    json={"message": message},
                    timeout=self.timeout
                )
                
                if broadcast_response.status_code == 200:
                    logger.info("Message broadcasted to teleprompter successfully")
                    return True
                else:
                    logger.warning(f"Broadcast failed: {broadcast_response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error broadcasting to teleprompter: {e}")
            return False

# Global manager instance
manager = TeleprompterManager()