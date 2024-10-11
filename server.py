import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv
from websocket_routes import websocket_endpoint

load_dotenv()

app = FastAPI()

# Enable CORS for local development
dev_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=dev_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket route
app.websocket("/ws")(websocket_endpoint)
