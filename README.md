# 🚀 FastAPI + LangGraph + ChromaDB (Dockerized)

A minimal FastAPI service built with **Python 3.12-slim** and Docker.  
This guide explains exactly how your teammates can run it on their own machines.

---

## 🧩 1. Prerequisites

Before running:

- Install **Docker** (Desktop or Engine)
- Ensure **port 8000** is free

---

## ⚙️ 2. Environment Variables

Create a file named `.env` in the **project root** (same directory as your `Dockerfile`)  
—or simply copy from `.env.sample`—then fill in your credentials:

```env
# OpenAI Configuration
AZURE_LLM_NAME=gpt-4o
AZURE_EMBEDDING_NAME=text-embedding-3-small
AZURE_LLM_API_KEY=your-api-key-here
AZURE_EMBEDDING_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
```

## 🧱 3. Build the Docker Image

From the project root:

```bash
docker build -t dnd-gamemaster .
```

## 📥 4. Run Data Ingestion (First Time Setup)

Before starting the application, run the ingestion script to:
- Populate SQLite database with spells and classes
- Upload embeddings to ChromaDB

### Using Docker (Recommended):

```bash
docker-compose run --rm api python -m ingestion.ingest_pdf

(old)
docker-compose run --rm api python ingestion/ingestion_script.py all
```

### Without Docker:

```bash
python ingestion/ingestion_script.py all
```

This step ingest data into ChromaDB
- ✅ All monster manual data
- ✅ All player related data, including classes, races, skills, traits, items, spells
- ✅ The main story, Lost Mines of Phandelver

**Note**: This only needs to be run once (or when you want to refresh the data).

## ▶️ 5. Run the Container

Once the image is built and data is ingested, start the container:

```bash
docker run --name dnd-gamemaster -p 8000:8000 dnd-gamemaster
```

Or using docker-compose:

```bash
docker-compose up
```

The app will now be available at:
👉 http://localhost:8000

## 🔍 6. Verify It's Running

- Interactive Docs (Swagger UI): http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

Or test directly with curl:
```bash
curl http://localhost:8000/
```

## 🧰 7. Useful Commands

```bash
# Stop and remove the container
docker stop dnd-gamemaster && docker rm dnd-gamemaster

# Rebuild the image (after code or dependency changes)
docker build -t dnd-gamemaster .

# Follow logs
docker logs -f dnd-gamemaster

# Re-run ingestion (to refresh data)
docker-compose run --rm api python ingestion/ingestion_script.py all

# Clean up unused Docker images and containers
docker system prune -f
```

## 🧠 8. Troubleshooting

| Problem                                | Cause                                         | Fix                                                                     |
| -------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------- |
| `COPY failed: file not found .env`     | `.env` missing or excluded by `.dockerignore` | Create `.env` in project root                                           |
| Port 8000 already in use               | Another process using it                      | Run with a different port: `docker run -p 8080:8000 dnd-gamemaster`    |
| App can't access environment variables | `.env` missing at build time                  | Ensure `.env` exists before running `docker build`                      |
| No SRD files found                     | SRD files missing from repository             | Ensure `resource/srd/` folder contains all CSV and data files           |
| ChromaDB collection empty              | Ingestion not run                             | Run: `docker-compose run --rm api python ingestion/ingestion_script.py all` |

## 🧪 9. Run Locally (Without Docker, optional)

If you want to run directly on your host:

```bash
python -m venv .venv
# Activate:
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Run ingestion first
```
python ingestion/ingestion_script.py all

# Then start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
