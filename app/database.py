"""
Database setup for ChromaDB and SQLite integration.
"""

import os
import sqlite3
from pathlib import Path
import chromadb
from typing import Optional

# Environment variables
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "/data/chroma")
SQLITE_PATH = os.getenv("SQLITE_PATH", "/data/app.db")

# Ensure data directories exist
Path(CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)

class DatabaseManager:
    """Manages both ChromaDB and SQLite connections."""
    
    def __init__(self):
        self.chroma_client: Optional[chromadb.PersistentClient] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
    
    def get_chroma_client(self) -> chromadb.PersistentClient:
        """Get or create ChromaDB persistent client."""
        if self.chroma_client is None:
            self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        return self.chroma_client
    
    def get_sqlite_connection(self) -> sqlite3.Connection:
        """Get or create SQLite connection."""
        if self.sqlite_conn is None:
            self.sqlite_conn = sqlite3.connect(SQLITE_PATH)
            self.sqlite_conn.row_factory = sqlite3.Row  # Enable dict-like access
            self._init_sqlite_tables()
        return self.sqlite_conn
    
    def _init_sqlite_tables(self):
        """Initialize SQLite tables if they don't exist."""
        cursor = self.sqlite_conn.cursor()
        
        # Example tables for your game master app
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_session_id INTEGER,
                name TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_session_id) REFERENCES game_sessions (id)
            )
        """)
        
        self.sqlite_conn.commit()
    
    def close_connections(self):
        """Close all database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_chroma_client():
    """Get ChromaDB client."""
    return db_manager.get_chroma_client()

def get_sqlite_connection():
    """Get SQLite connection."""
    return db_manager.get_sqlite_connection()
