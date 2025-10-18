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
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
AZURE_DEPLOYMENT_NAME="GPT-4o-mini"
AZURE_EMBEDDING_NAME="text-embedding-3-small"
AZURE_EMBEDDING_API_KEY=""
```
## 🧱 3. Build the Docker Image

From the project root:

```
docker build -t dnd-gamemaster .
```
## ▶️ 4. Run the Container

Once the image is built, start the container:
```
docker run --name dnd-gamemaster -p 8000:8000 my-fastapi-app
```

The app will now be available at:
👉 http://localhost:8000

## 🔍  5. Verify It’s Running
* Interactive Docs (Swagger UI): http://localhost:8000/docs
* OpenAPI JSON: http://localhost:8000/openapi.json

Or test directly with curl:
`
curl http://localhost:8000/
`
## 🧰 6. Useful Commands
```
# Stop and remove the container
docker stop my-fastapi-app && docker rm my-fastapi-app

# Rebuild the image (after code or dependency changes)
docker build -t my-fastapi-app .

# Follow logs
docker logs -f my-fastapi-app

# Clean up unused Docker images and containers
docker system prune -f
```

## 🧠 7. Troubleshooting
| Problem                                | Cause                                         | Fix                                                                 |
| -------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------- |
| `COPY failed: file not found .env`     | `.env` missing or excluded by `.dockerignore` | Create `.env` in project root                                       |
| Port 8000 already in use               | Another process using it                      | Run with a different port: `docker run -p 8080:8000 my-fastapi-app` |
| App can’t access environment variables | `.env` missing at build time                  | Ensure `.env` exists before running `docker build`                  |

## 🧪 8. Run Locally (Without Docker, optional)

If you want to run directly on your host:

```
python -m venv .venv
# Activate:
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```