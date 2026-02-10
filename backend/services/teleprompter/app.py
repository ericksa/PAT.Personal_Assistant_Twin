# services/teleprompter/app.py
import asyncio
import websockets
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Teleprompter Service")

# Serve static files for teleprompter frontend
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

class BroadcastRequest(BaseModel):
    message: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.current_text = "Ready for your interview"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current text immediately
        await websocket.send_json({"type": "text", "content": self.current_text})
        logger.info("Teleprompter connected")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Teleprompter disconnected")

    async def broadcast(self, message: str):
        self.current_text = message
        disconnected = []
        
        # Broadcast to all connected WebSocket clients
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "text", 
                    "content": message,
                    "timestamp": str(asyncio.get_event_loop().time())
                })
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.append(connection)

        # Cleanup disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Endpoint for agent service to broadcast messages"""
    try:
        await manager.broadcast(request.message)
        return {
            "status": "broadcasted", 
            "message": request.message[:100] + "...", 
            "connections": len(manager.active_connections)
        }
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """Serve the teleprompter frontend"""
    return FileResponse("/app/static/index.html")

@app.get("/display")
async def display():
    """Direct link to the teleprompter display"""
    return FileResponse("/app/static/index.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(manager.active_connections)}

# Keep server running
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Teleprompter Service on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)