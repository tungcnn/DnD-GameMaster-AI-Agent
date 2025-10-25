from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

class ChromaService:
    def __init__(self, collection_name: str = "spells", openai_service=None):
        """
        Initialize ChromaDB service for storing spell embeddings with metadata.
        
        Args:
            collection_name: Name of the collection
            openai_service: Optional OpenAI service for generating query embeddings
        """
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        chroma_db_path = project_root / "resource" / "chroma_db"
        
        # Ensure directory exists
        chroma_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(chroma_db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        self.collection_name = collection_name
        self.openai_service = openai_service
    
    def search_spells(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for spells using semantic similarity.
        Uses OpenAI embeddings if available, otherwise falls back to ChromaDB's default.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of matching spells with similarity scores
        """
        try:
            # Use OpenAI to generate query embedding if service is available
            if self.openai_service:
                query_embedding = self.openai_service.generate_embedding(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where
                )
            else:
                # Fallback to ChromaDB's default embedding
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where
                )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'id': results['ids'][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching spells: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_spells": count,
                "status": "active"
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}

# Create a global instance
chroma_service = ChromaService()
