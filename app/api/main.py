from fastapi import FastAPI
from ..database import get_chroma_client, get_sqlite_connection
import chromadb

app = FastAPI(title="LLM Game Master API")


@app.get("/")
async def root():
    return {"message": "LLM Game Master API", "status": "running"}


@app.get("/start-game")
async def start_game(name: str):
    """Start a new game session and add player."""
    try:
        # SQLite: Store game session and player
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # Create game session
        cursor.execute(
            "INSERT INTO game_sessions (name) VALUES (?)",
            (f"Game for {name}",)
        )
        game_session_id = cursor.lastrowid
        
        # Add player
        cursor.execute(
            "INSERT INTO players (game_session_id, name) VALUES (?, ?)",
            (game_session_id, name)
        )
        conn.commit()
        
        # ChromaDB: Store game context (example)
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection("game_contexts")
        
        collection.add(
            documents=[f"Player {name} joined game session {game_session_id}"],
            ids=[f"player_{name}_{game_session_id}"],
            metadatas=[{"player": name, "session_id": game_session_id, "action": "join"}]
        )
        
        return {
            "message": f"Player {name} joined game session {game_session_id} successfully",
            "game_session_id": game_session_id
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/game-sessions")
async def get_game_sessions():
    """Get all active game sessions."""
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gs.id, gs.name, gs.created_at, gs.status,
                   COUNT(p.id) as player_count
            FROM game_sessions gs
            LEFT JOIN players p ON gs.id = p.game_session_id
            WHERE gs.status = 'active'
            GROUP BY gs.id, gs.name, gs.created_at, gs.status
            ORDER BY gs.created_at DESC
        """)
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "status": row["status"],
                "player_count": row["player_count"]
            })
        
        return {"game_sessions": sessions}
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint that tests both databases."""
    try:
        # Test SQLite
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM game_sessions")
        session_count = cursor.fetchone()[0]
        
        # Test ChromaDB
        chroma_client = get_chroma_client()
        collections = chroma_client.list_collections()
        
        return {
            "status": "healthy",
            "sqlite": {
                "connected": True,
                "game_sessions": session_count
            },
            "chromadb": {
                "connected": True,
                "collections": len(collections)
            }
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
