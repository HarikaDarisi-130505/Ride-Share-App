from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .routers import auth, rides, requests, chat, ratings, locations
from .websockets import manager
from fastapi import WebSocket, WebSocketDisconnect
from .database import SessionLocal

from .database import engine, Base, ensure_runtime_schema

# Create database tables
Base.metadata.create_all(bind=engine)
ensure_runtime_schema()

app = FastAPI(title="VIT-AP Ride Share")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rides.router)
app.include_router(requests.router)
app.include_router(chat.router)
app.include_router(ratings.router)
app.include_router(locations.router)

@app.websocket("/ws/ride/{ride_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, ride_id: int, user_id: int):
    await manager.manager.connect(websocket, ride_id)
    try:
        while True:
            data = await websocket.receive_json()
            # data = { type: "chat" | "location", content: ... }
            
            if data.get("type") == "chat":
                # Save to DB
                db = SessionLocal()
                try:
                    msg = models.ChatMessage(
                        ride_id=ride_id, 
                        user_id=user_id, 
                        message=data.get("message")
                    )
                    db.add(msg)
                    db.commit()
                finally:
                    db.close()
            
            # Broadcast to everyone
            await manager.manager.broadcast(data, ride_id)
            
    except WebSocketDisconnect:
        manager.manager.disconnect(websocket, ride_id)

@app.get("/")
def read_root():
    return {"message": "Welcome to VIT-AP Ride Share API"}
