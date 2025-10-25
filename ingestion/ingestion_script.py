"""
Main ingestion script - CLI entry point for spell data ingestion.
Handles CSV reading, SQLite ingestion, ChromaDB batch processing, and testing.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.sqlite_ingestion import SQLiteIngestion
from ingestion.chroma_ingestion import ChromaIngestion
from ingestion.ingestion_helper import print_separator
from ingestion.gdrive_downloader import download_srd_files

# Default CSV paths (adjust for Docker or local environment)
SPELLS_CSV_PATH = "/app/resource/srd/spells.csv"
CLASSES_CSV_PATH = "/app/resource/srd/classes.csv"


def ensure_srd_files():
    """
    Ensure SRD files are available by downloading from Google Drive if configured.
    """
    print_separator("Checking SRD Files")
    
    try:
        success = download_srd_files(force=False)
        if success:
            print("✅ All SRD files are ready\n")
        else:
            print("⚠️  Some files may be missing. Proceeding with available files...\n")
        return success
    except Exception as e:
        print(f"⚠️  Error checking SRD files: {e}")
        print("Proceeding with available local files...\n")
        return False


def ingest_spells_to_sqlite(csv_path: str = SPELLS_CSV_PATH):
    """
    Ingest spells from CSV to SQLite database.
    
    Args:
        csv_path: Path to spells CSV file
    """
    print_separator("Spells CSV to SQLite Ingestion")
    
    try:
        sqlite_ingestion = SQLiteIngestion()
        spells_data = sqlite_ingestion.ingest_spells_from_csv(csv_path)
        
        print(f"\n✅ Successfully ingested {len(spells_data)} spells to SQLite")
        return spells_data
        
    except Exception as e:
        print(f"❌ Error during spells ingestion: {e}")
        raise


def ingest_classes_to_sqlite(csv_path: str = CLASSES_CSV_PATH):
    """
    Ingest classes from CSV to SQLite database.
    
    Args:
        csv_path: Path to classes CSV file
    """
    print_separator("Classes CSV to SQLite Ingestion")
    
    try:
        sqlite_ingestion = SQLiteIngestion()
        classes_data = sqlite_ingestion.ingest_classes_from_csv(csv_path)
        
        print(f"\n✅ Successfully ingested {len(classes_data)} classes to SQLite")
        print("\nIngested classes:")
        for class_data in classes_data:
            print(f"  • {class_data['name']:15s} (index: {class_data['index']:10s}, health: {class_data['health']})")
        
        return classes_data
        
    except Exception as e:
        print(f"❌ Error during classes ingestion: {e}")
        raise


def upload_batch_to_chromadb(
    batch_file: str = None,
    metadata_file: str = None,
    collection_name: str = "spells"
):
    """
    Upload OpenAI Batch API results to ChromaDB.
    
    Args:
        batch_file: Path to batch results JSONL file
        metadata_file: Path to metadata JSON file
        collection_name: ChromaDB collection name
    """
    print_separator("Upload Batch Results to ChromaDB")
    
    try:
        chroma_ingestion = ChromaIngestion()
        
        # Auto-detect files if not provided
        if not batch_file:
            batch_dir = Path("resource/srd")
            batch_files = list(batch_dir.glob("*embedding*.jsonl"))
            if batch_files:
                batch_file = str(sorted(batch_files, key=lambda x: x.stat().st_mtime)[-1])
            else:
                print("❌ Error: No batch result file found in resource/srd/")
                return None
        
        if not metadata_file:
            batch_dir = Path("resource/srd")
            metadata_files = list(batch_dir.glob("*metadata*.json"))
            if metadata_files:
                metadata_file = str(sorted(metadata_files, key=lambda x: x.stat().st_mtime)[-1])
            else:
                print("❌ Error: No metadata file found in resource/srd/")
                return None
        
        print(f"Batch file: {batch_file}")
        print(f"Metadata file: {metadata_file}")
        print(f"Collection: {collection_name}\n")
        
        # Verify files exist
        if not Path(batch_file).exists():
            print(f"❌ Error: Batch file not found: {batch_file}")
            return None
        
        if not Path(metadata_file).exists():
            print(f"❌ Error: Metadata file not found: {metadata_file}")
            return None
        
        # Upload to ChromaDB
        result = chroma_ingestion.upload_batch_results_to_chromadb(
            batch_result_file=batch_file,
            metadata_file=metadata_file,
            collection_name=collection_name
        )
        
        print_separator("Upload Result")
        
        if result.get("success"):
            print("✅ SUCCESS!")
            print(f"   Collection: {result['collection_name']}")
            print(f"   Total uploaded: {result['total_uploaded']}")
            print(f"   Failed: {result['failed']}")
        else:
            print("❌ FAILED!")
            print(f"   Error: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error uploading to ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_ingestion():
    """
    Run complete ingestion workflow: ingest spells, classes, and upload embeddings.
    """
    print_separator("Complete Ingestion Workflow", "=")
    
    # Step 0: Ensure SRD files are downloaded
    ensure_srd_files()
    
    success_count = 0
    total_steps = 3
    
    try:
        # Step 1: Ingest spells
        print("\n[1/3] Ingesting spells...")
        spells_data = ingest_spells_to_sqlite()
        if spells_data:
            success_count += 1
            print(f"✅ Step 1 complete: {len(spells_data)} spells ingested")
        
        # Step 2: Ingest classes
        print("\n[2/3] Ingesting classes...")
        classes_data = ingest_classes_to_sqlite()
        if classes_data:
            success_count += 1
            print(f"✅ Step 2 complete: {len(classes_data)} classes ingested")
        
        # Step 3: Upload batch embeddings
        print("\n[3/3] Uploading batch embeddings to ChromaDB...")
        result = upload_batch_to_chromadb()
        if result and result.get("success"):
            success_count += 1
            print(f"✅ Step 3 complete: {result['total_uploaded']} embeddings uploaded")
        
        # Summary
        print_separator("Ingestion Summary")
        print(f"Completed {success_count}/{total_steps} steps")
        
        if success_count == total_steps:
            print("🎉 All ingestion steps completed successfully!")
        else:
            print("⚠️  Some steps failed. Check the logs above for details.")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion workflow: {e}")
        import traceback
        traceback.print_exc()


def show_help():
    """Display help message with all available commands."""
    print("""
Usage: python ingestion_script.py <command> [options]

Commands:
  all                 Run complete workflow: ingest spells, classes, and upload embeddings
  ingest-spells       Ingest spells CSV to SQLite
  ingest-classes      Ingest classes CSV to SQLite
  upload              Upload OpenAI batch results to ChromaDB
                      [--batch <file>] [--metadata <file>] [--collection <name>]
  help                Show this help message

Examples:
  # Run everything at once (recommended)
  python ingestion_script.py all
  
  # Or run individual steps
  python ingestion_script.py ingest-spells
  python ingestion_script.py ingest-classes
  python ingestion_script.py upload
  
  # Upload with custom files
  python ingestion_script.py upload --batch results.jsonl --metadata meta.json

Google Drive Integration:
  Files are automatically downloaded from Google Drive if configured.
  See GDRIVE_SETUP.md for configuration instructions.
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default: show help
        show_help()
        sys.exit(0)
    
    command = sys.argv[1]
    
    try:
        if command == "all":
            # Run complete workflow
            run_all_ingestion()
        
        elif command == "ingest-spells":
            # Ensure files are available
            ensure_srd_files()
            # Ingest spells CSV to SQLite
            csv_path = sys.argv[2] if len(sys.argv) > 2 else SPELLS_CSV_PATH
            ingest_spells_to_sqlite(csv_path)
        
        elif command == "ingest-classes":
            # Ensure files are available
            ensure_srd_files()
            # Ingest classes CSV to SQLite
            csv_path = sys.argv[2] if len(sys.argv) > 2 else CLASSES_CSV_PATH
            ingest_classes_to_sqlite(csv_path)
        
        elif command == "upload":
            # Ensure files are available
            ensure_srd_files()
            # Upload batch results to ChromaDB
            batch_file = None
            metadata_file = None
            collection = "spells"
            
            # Parse optional arguments
            i = 2
            while i < len(sys.argv):
                if sys.argv[i] == "--batch" and i + 1 < len(sys.argv):
                    batch_file = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--metadata" and i + 1 < len(sys.argv):
                    metadata_file = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--collection" and i + 1 < len(sys.argv):
                    collection = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            upload_batch_to_chromadb(batch_file, metadata_file, collection)
        
        elif command == "help":
            # Show help
            show_help()
        
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
