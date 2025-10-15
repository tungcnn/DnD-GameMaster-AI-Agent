# 🚀 DnD AI Dungeon Master Backend


## Install
pip install -r requirements.txt

### Env
Create .env file with these content
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_DEPLOYMENT_NAME="GPT-4o-mini"
AZURE_EMBEDDING_NAME="text-embedding-3-small"
AZURE_EMBEDDING_API_KEY=<your-api-key>

### Run
#### Activate local dependency mode if you used virtual environment
- venv\Scripts\activate.bat (window)
- source venv/bin/activate (mac)
#### Run server
uvicorn app.main:app --reload
👉 http://localhost:8000/docs