"""
ChromaDB ingestion and management for spell embeddings.
Handles batch API processing, embedding storage, and search testing.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ChromaService import ChromaService
from app.services.OpenAPIService import openai_service


class ChromaIngestion:
    def __init__(self, batch_dir: str = "resource/srd"):
        """
        Initialize ChromaDB ingestion service.
        
        Args:
            batch_dir: Directory for batch result files (default: resource/srd)
        """
        self.batch_dir = Path(batch_dir)
        self.batch_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_batch_results_to_chromadb(
        self, 
        batch_result_file: str, 
        metadata_file: str,
        collection_name: str = "spells"
    ) -> Dict[str, Any]:
        """
        Process OpenAI Batch API results and upload to ChromaDB with metadata.
        
        Args:
            batch_result_file: Path to the JSONL file with OpenAI batch results
            metadata_file: Path to the metadata JSON file
            collection_name: Name of the ChromaDB collection
            
        Returns:
            Dictionary with upload statistics
        """
        try:
            # Load metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            # Initialize ChromaDB
            chroma_service = ChromaService(collection_name)
            
            # Process batch results
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            with open(batch_result_file, 'r', encoding='utf-8') as f:
                for line in f:
                    result = json.loads(line.strip())
                    
                    # Extract data from OpenAI response format
                    custom_id = result.get('custom_id')
                    
                    # Handle both success and error cases
                    if result.get('response') and result['response'].get('status_code') == 200:
                        body = result['response'].get('body', {})
                        embedding_data = body.get('data', [{}])[0]
                        embedding = embedding_data.get('embedding')
                        
                        if embedding and custom_id in metadata_dict:
                            # Get the original document text and metadata
                            spell_metadata = metadata_dict[custom_id].copy()
                            doc_text = spell_metadata.pop('document_text', f"Spell: {spell_metadata['name']}")
                            
                            # Clean metadata - ChromaDB doesn't accept None values
                            cleaned_metadata = {}
                            for key, value in spell_metadata.items():
                                if value is None or value == "":
                                    # For string fields, use empty string
                                    if key in ['damage', 'heal', 'cast_class', 'effect_kind', 'description']:
                                        cleaned_metadata[key] = ""
                                    # Boolean fields should be False if None
                                    elif key in ['has_damage', 'has_heal']:
                                        cleaned_metadata[key] = False
                                    # Skip None for other fields or use empty string
                                    elif isinstance(value, str) or value is None:
                                        cleaned_metadata[key] = ""
                                else:
                                    cleaned_metadata[key] = value
                            
                            documents.append(doc_text)
                            embeddings.append(embedding)
                            metadatas.append(cleaned_metadata)
                            ids.append(custom_id)
                    else:
                        # Log error for this item
                        error = result.get('error', {})
                        print(f"Error for {custom_id}: {error}")
            
            # Upload to ChromaDB
            if embeddings:
                chroma_service.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                
                print(f"Successfully uploaded {len(embeddings)} embeddings to ChromaDB collection '{collection_name}'")
                
                return {
                    "success": True,
                    "collection_name": collection_name,
                    "total_uploaded": len(embeddings),
                    "total_processed": len(ids),
                    "failed": 0
                }
            else:
                return {
                    "success": False,
                    "error": "No valid embeddings found in batch results"
                }
                
        except Exception as e:
            print(f"Error processing batch results: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get statistics about batch result files in srd directory.
        """
        try:
            jsonl_files = list(self.batch_dir.glob("*embedding*.jsonl"))
            json_files = list(self.batch_dir.glob("*metadata*.json"))
            
            return {
                "batch_directory": str(self.batch_dir),
                "batch_result_files": len(jsonl_files),
                "metadata_files": len(json_files),
                "status": "ready"
            }
        except Exception as e:
            print(f"Error getting batch stats: {e}")
            return {"error": str(e)}


# Testing functions
def test_chromadb(collection_name: str = "spells", query: str = None):
    """
    Test ChromaDB collection with semantic search.
    
    Args:
        collection_name: Name of the collection to test
        query: Optional search query. If None, runs comprehensive tests.
    """
    try:
        chroma = ChromaService(collection_name=collection_name, openai_service=openai_service)
        
        if query:
            # Quick search mode
            print(f"\n{'='*70}")
            print(f"🔍 Search: '{query}'")
            print(f"{'='*70}\n")
            print("🔧 Using OpenAI text-embedding-3-small for query embedding\n")
            
            results = chroma.search_spells(query, n_results=5)
            
            if results:
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    distance = result['distance']
                    similarity = 1 - distance
                    
                    print(f"{i}. {metadata.get('name', 'Unknown')} (similarity: {similarity:.3f})")
                    print(f"   Classes: {metadata.get('cast_class', 'N/A')}")
                    print(f"   Effect: {metadata.get('effect_kind', 'N/A')}")
                    
                    if metadata.get('damage'):
                        print(f"   💥 Damage: {metadata.get('damage')}")
                    if metadata.get('heal'):
                        print(f"   💚 Heal: {metadata.get('heal')}")
                    
                    # Show description if available (truncate if too long)
                    description = metadata.get('description', '')
                    if description:
                        desc_preview = description[:100] + "..." if len(description) > 100 else description
                        print(f"   📝 {desc_preview}")
                    print()
            else:
                print("No results found")
        else:
            # Comprehensive test mode
            print(f"\n{'='*70}")
            print(f"🧪 ChromaDB Collection Test")
            print(f"{'='*70}\n")
            
            # Test 1: Collection stats
            count = chroma.collection.count()
            print(f"✅ Collection: '{collection_name}'")
            print(f"✅ Total spells: {count}")
            
            if count == 0:
                print("⚠️  WARNING: Collection is empty!")
                return
            
            # Test 2: Sample search
            print(f"\n🔍 Testing semantic search...")
            results = chroma.search_spells("fire damage", n_results=3)
            
            if results:
                print(f"✅ Found {len(results)} results for 'fire damage':")
                for i, result in enumerate(results, 1):
                    metadata = result['metadata']
                    distance = result['distance']
                    similarity = 1 - distance
                    print(f"  {i}. {metadata.get('name')} (similarity: {similarity:.3f})")
            
            print(f"\n{'='*70}")
            print(f"✅ ChromaDB is working correctly!")
            print(f"{'='*70}\n")
            
    except Exception as e:
        print(f"❌ Error testing ChromaDB: {e}")
        import traceback
        traceback.print_exc()


# Create a global instance
chroma_ingestion = ChromaIngestion()

