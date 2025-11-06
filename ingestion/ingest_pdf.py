import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings 
# from app.config.LoadAppConfig import LoadAppConfig

load_dotenv()
# CFG = LoadAppConfig()

SOURCE_DIRECTORY = "resource/srd" 
CHROMA_DB_DIR = "resource/chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Helper Function ---
def print_separator(title, char="-"):
    """Prints a clear separator line."""
    print(f"\n{char * 5} {title} {char * 5}\n")

# --- Main Ingestion Logic ---
def ingest_files(
    pdf_paths: list[str],
    chunk_size: int,
    chunk_overlap: int,
):
    """
    Ingests a list of PDF files, creating a unique ChromaDB collection for each one.
    """
    print_separator("Multi-PDF to Separate ChromaDB Collections")

    if not pdf_paths:
        print("⚠️ No PDF files found to ingest. Exiting.")
        return 0

    try:
        # 0. Set up Embedding Function
        print("Initializing Embedding Model...")

        embeddings = OpenAIEmbeddings(
            model=os.getenv("AZURE_EMBEDDING_NAME"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_EMBEDDING_API_KEY")
        )
        
        # Initialize the splitter once
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap, 
            separators=["\n\n", "\n", " ", ""]
        )

        total_chunks_uploaded = 0
        
        for i, pdf_path in enumerate(pdf_paths):
            source_file_name = Path(pdf_path).name
            
            # Create a clean, unique collection name from the filename (no extension)
            collection_name = source_file_name.replace('.', '_').replace('-', '_').lower().removesuffix('_pdf')
            
            print_separator(f"[{i+1}/{len(pdf_paths)}] Processing File: {source_file_name}")
            print(f"-> Target Collection: '{collection_name}'")
            
            # 1. Load the Document
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # 2. Split the Document into Chunks
            chunks = text_splitter.split_documents(documents)
            
            # CRITICAL: Attach the source file name to EVERY chunk for traceability
            for chunk in chunks:
                chunk.metadata['source_file'] = source_file_name
            
            print(f"  -> Created {len(chunks)} text chunks.")

            # 3. Ingest into ChromaDB
            print(f"  -> Ingesting {len(chunks)} chunks...")
            
            # Create a NEW Chroma instance/collection for each PDF
            vectordb = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                collection_name=collection_name,
                persist_directory=CHROMA_DB_DIR
            )
            # The collection is persisted upon creation/update

            total_chunks_uploaded += len(chunks)
            print(f"  ✅ SUCCESS: {len(chunks)} chunks uploaded to '{collection_name}'.")


        print_separator("Final Ingestion Summary")
        print(f"🎉 All {len(pdf_paths)} files processed.")
        print(f"Total chunks uploaded across all collections: {total_chunks_uploaded}")
        return total_chunks_uploaded

    except Exception as e:
        print(f"❌ Error during PDF ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 0


def show_help():
    """Display help message with all available options."""
    print(f"""
Usage: python {Path(__file__).name} [options]

This script loads ALL PDF files from '{SOURCE_DIRECTORY}' and creates a 
SEPARATE ChromaDB collection for each one (e.g., 'phb.pdf' -> 'phb' collection).

Options:
  --dir <path>        Directory to search for PDFs (default: {SOURCE_DIRECTORY})
  --chunk <size>      Chunk size in characters (default: {CHUNK_SIZE})
  --overlap <size>    Chunk overlap in characters (default: {CHUNK_OVERLAP})
  --help              Show this help message

Example:
  # Ingest all PDFs in the default directory:
  python {Path(__file__).name}
  
  # Ingest all PDFs from a custom directory with smaller chunks:
  python {Path(__file__).name} --dir custom_rules/ --chunk 800
    """)


if __name__ == "__main__":
    
    # Initialize parameters from defaults
    pdf_dir = SOURCE_DIRECTORY
    chunk_size = 1000
    chunk_overlap = 200
    
    # Parse command-line arguments (Modified to accept --dir)
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        try:
            if arg == "--dir":
                pdf_dir = sys.argv[i + 1]
                i += 2
            elif arg == "--chunk":
                chunk_size = int(sys.argv[i + 1])
                i += 2
            elif arg == "--overlap":
                chunk_overlap = int(sys.argv[i + 1])
                i += 2
            elif arg == "--help":
                show_help()
                sys.exit(0)
            else:
                i += 1
        except IndexError:
            print(f"❌ Missing value for argument: {arg}")
            show_help()
            sys.exit(1)
        except ValueError:
            print(f"❌ Invalid integer value provided for chunk or overlap size.")
            sys.exit(1)

    # Find all PDF files in the target directory
    pdf_paths = [str(p) for p in Path(pdf_dir).glob("*.pdf")]
    
    ingest_files(pdf_paths, chunk_size, chunk_overlap)