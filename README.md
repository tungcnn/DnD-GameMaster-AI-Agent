# 🧠 LLM Game Master

A FastAPI + LangGraph + ChromaDB + SQLite project running in Docker.

## 🚀 Quick Start

```bash
git clone https://github.com/yourusername/llm-game-master.git
cd llm-game-master

# Copy environment template
cp .env.sample .env

# Build & run
docker compose up --build

FastAPI runs on: http://localhost:8000
```

## 🧩 Tech Stack

```FastAPI — Backend framework

LangGraph — LLM flow orchestration

ChromaDB — Vector store

SQLite — Lightweight relational database

Docker Compose — Container orchestration for consistent setup
```
## ⚙️ Development

```Source code is mounted as a live volume:

Edit code locally → auto-reloads in container

Persistent data stored in:

/data → ChromaDB

/db → SQLite
```