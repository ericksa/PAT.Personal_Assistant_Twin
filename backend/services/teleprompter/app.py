# services/teleprompter/app.py
import asyncio
import websockets
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.current_text = ""

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Teleprompter connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Teleprompter disconnected")

    async def broadcast(self, message: str):
        self.current_text = message
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.active_connections.remove(connection)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"status": "teleprompter_service_running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(manager.active_connections)}


from pydantic import BaseModel


class BroadcastRequest(BaseModel):
    message: str


@app.post("/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Endpoint for agent service to broadcast messages"""
    try:
        await manager.broadcast(request.message)
        return {"status": "broadcasted", "message": request.message[:100] + "...", "connections": len(manager.active_connections)}
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return {"status": "error", "message": str(e)}


# Keep server running
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Teleprompter Service on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)