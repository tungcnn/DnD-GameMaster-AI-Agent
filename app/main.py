from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import ChatController

app = FastAPI(title="DnD AI Dungeon Master")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ChatController.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "DnD AI GM is running"}