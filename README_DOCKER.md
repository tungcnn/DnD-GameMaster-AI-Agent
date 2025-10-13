## Run with Docker (Cursor or PyCharm)

This project is a FastAPI app with embedded ChromaDB and SQLite databases.

### 1) Prerequisites

- Docker Desktop installed and running
- Optional: `curl` for health checks

### 2) Files added

- `Dockerfile`: builds a Python 3.12 image and runs uvicorn
- `docker-compose.yml`: single service with embedded databases
- `.dockerignore`: prevents copying caches and local env files
- `app/database.py`: database manager for ChromaDB and SQLite

### 3) Quick start (production)

```bash
docker compose up --build
```

This starts:
- FastAPI app at `http://localhost:8000/`
- Embedded ChromaDB (persistent to `/data/chroma`)
- Embedded SQLite (persistent to `/data/app.db`)

To stop:

```bash
docker compose down
```

### 4) Development mode (with hot reload)

```bash
# Uncomment the command line in docker-compose.yml for hot reload
docker compose up --build
```

Or modify the docker-compose.yml to include:
```yaml
command: uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5) Environment variables

Default values (can be overridden in docker-compose.yml):
- `CHROMA_DB_DIR=/data/chroma`
- `SQLITE_PATH=/db/app.db`

### 6) Data persistence

- **SQLite**: Game sessions, players, and relational data stored in `./db/app.db`
- **ChromaDB**: Vector embeddings for game contexts and LLM interactions stored in `./data/chroma/`
- **Storage**: Both databases use bind mounts to your local directories

### 7) API Endpoints

- Root: `GET http://localhost:8000/`
- Start game: `GET http://localhost:8000/start-game?name=PlayerName`
- Game sessions: `GET http://localhost:8000/game-sessions`
- Health check: `GET http://localhost:8000/health`

### 8) Use in Cursor

1. Open this folder in Cursor.
2. Open the built-in terminal and run: `docker compose up --build`.
3. Use the "REST Client" (or your browser) to call `http://localhost:8000/`.
4. For hot reload, uncomment the command line in docker-compose.yml.

### 9) Use in PyCharm

Option A: Docker Compose run configuration

1. Open the project in PyCharm.
2. Add a new Run/Debug Configuration → Docker Compose.
3. Set `docker-compose.yml` as the file, service `api`, and enable "Build before run".
4. Run/Debug to start the container.

Option B: Dockerfile run configuration

1. Add a Docker run configuration using the `Dockerfile` with port mapping `8000:8000`.
2. Set the command to `uvicorn app.api.main:app --host 0.0.0.0 --port 8000` if you override defaults.

Option C: Local (without Docker)

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: . .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 10) Database Usage

**SQLite** (for structured data):
```python
from app.database import get_sqlite_connection
conn = get_sqlite_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM game_sessions")
```

**ChromaDB** (for vector embeddings):
```python
from app.database import get_chroma_client
client = get_chroma_client()
collection = client.get_or_create_collection("my_collection")
```

### 11) Common issues

- Port already in use: change the published port, e.g., `- "8080:8000"`.
- Large dependency set: first build may take time; subsequent builds are cached.
- Database connection issues: check the `/health` endpoint to verify both databases are working.
- Data persistence: SQLite data is in `./db/` and ChromaDB data is in `./data/chroma/` directories.