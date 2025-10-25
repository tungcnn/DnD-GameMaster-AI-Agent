"""
Google Drive file downloader for SRD resources.
Downloads files from Google Drive before ingestion.
"""

import os
from pathlib import Path
from typing import Dict, List

try:
    import gdown
except ImportError:
    gdown = None


class GDriveDownloader:
    """Handle downloading files from Google Drive."""
    
    def __init__(self, srd_dir: str = "resource/srd"):
        """
        Initialize GDrive downloader.
        
        Args:
            srd_dir: Directory to store downloaded files
        """
        self.srd_dir = Path(srd_dir)
        self.srd_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for folder URL first (simpler approach)
        self.folder_url = os.getenv("GDRIVE_SRD_FOLDER")
        
        # Google Drive file mappings (file_id or share_url -> local filename)
        # These should be set via environment variables or config
        self.file_mappings = self._load_file_mappings()
    
    def _load_file_mappings(self) -> Dict[str, str]:
        """
        Load Google Drive file mappings from environment variables.
        
        Expected format:
            GDRIVE_SPELLS_CSV: Google Drive file ID or share URL
            GDRIVE_CLASSES_CSV: Google Drive file ID or share URL
            GDRIVE_BATCH_JSONL: Google Drive file ID or share URL
            GDRIVE_METADATA_JSON: Google Drive file ID or share URL
        
        Returns:
            Dictionary mapping file IDs/URLs to local filenames
        """
        mappings = {}
        
        # Spells CSV
        if os.getenv("GDRIVE_SPELLS_CSV"):
            mappings[os.getenv("GDRIVE_SPELLS_CSV")] = "spells.csv"
        
        # Classes CSV
        if os.getenv("GDRIVE_CLASSES_CSV"):
            mappings[os.getenv("GDRIVE_CLASSES_CSV")] = "classes.csv"
        
        # Batch embeddings JSONL
        if os.getenv("GDRIVE_BATCH_JSONL"):
            mappings[os.getenv("GDRIVE_BATCH_JSONL")] = "batch_spells_embedding_output.jsonl"
        
        # Metadata JSON
        if os.getenv("GDRIVE_METADATA_JSON"):
            mappings[os.getenv("GDRIVE_METADATA_JSON")] = os.getenv("GDRIVE_METADATA_JSON_FILENAME", "spell_embeddings_metadata.json")
        
        return mappings
    
    def _extract_file_id(self, url_or_id: str) -> str:
        """
        Extract file ID from Google Drive URL or return ID as-is.
        
        Args:
            url_or_id: Google Drive share URL or file ID
            
        Returns:
            File ID
        """
        # If it's already a file ID (no slashes or http)
        if '/' not in url_or_id and 'http' not in url_or_id:
            return url_or_id
        
        # Extract from various URL formats
        # https://drive.google.com/file/d/FILE_ID/view?usp=sharing
        # https://drive.google.com/open?id=FILE_ID
        # https://drive.google.com/drive/folders/FOLDER_ID?usp=sharing
        if '/file/d/' in url_or_id:
            return url_or_id.split('/file/d/')[1].split('/')[0]
        elif '/folders/' in url_or_id:
            return url_or_id.split('/folders/')[1].split('?')[0]
        elif 'id=' in url_or_id:
            return url_or_id.split('id=')[1].split('&')[0]
        
        return url_or_id
    
    def download_folder(self, folder_url: str, force: bool = False) -> bool:
        """
        Download entire folder from Google Drive.
        
        Args:
            folder_url: Google Drive folder URL or ID
            force: Force re-download even if files exist
            
        Returns:
            True if download successful, False otherwise
        """
        if gdown is None:
            print("⚠️  Warning: gdown not installed. Run: pip install gdown")
            return False
        
        try:
            folder_id = self._extract_file_id(folder_url)
            folder_download_url = f"https://drive.google.com/drive/folders/{folder_id}"
            
            print(f"📂 Downloading folder from Google Drive...")
            print(f"   Folder ID: {folder_id}")
            print(f"   Target: {self.srd_dir}\n")
            
            # Download folder contents
            gdown.download_folder(
                url=folder_download_url,
                output=str(self.srd_dir),
                quiet=False,
                use_cookies=False
            )
            
            print(f"\n✅ Folder downloaded successfully to {self.srd_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading folder: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def download_file(self, url_or_id: str, output_filename: str, force: bool = False) -> bool:
        """
        Download a single file from Google Drive.
        
        Args:
            url_or_id: Google Drive file ID or share URL
            output_filename: Name for the downloaded file
            force: Force re-download even if file exists
            
        Returns:
            True if download successful, False otherwise
        """
        if gdown is None:
            print("⚠️  Warning: gdown not installed. Run: pip install gdown")
            return False
        
        output_path = self.srd_dir / output_filename
        
        # Skip if file exists and not forcing
        if output_path.exists() and not force:
            print(f"  ✓ {output_filename} already exists (skipping)")
            return True
        
        try:
            file_id = self._extract_file_id(url_or_id)
            url = f"https://drive.google.com/uc?id={file_id}"
            
            print(f"  📥 Downloading {output_filename}...")
            gdown.download(url, str(output_path), quiet=False)
            print(f"  ✅ Downloaded {output_filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error downloading {output_filename}: {e}")
            return False
    
    def download_all(self, force: bool = False) -> Dict[str, bool]:
        """
        Download all configured files from Google Drive.
        
        Args:
            force: Force re-download even if files exist
            
        Returns:
            Dictionary mapping filenames to success status
        """
        # If folder URL is configured, use folder download (simpler)
        if self.folder_url:
            print("📂 Downloading entire SRD folder from Google Drive...\n")
            success = self.download_folder(self.folder_url, force)
            
            # Check which files were downloaded
            expected_files = [
                "spells.csv",
                "classes.csv", 
                "batch_spells_embedding_output.jsonl",
                "spell_embeddings_20251025_041254_metadata.json"
            ]
            
            results = {}
            for filename in expected_files:
                file_path = self.srd_dir / filename
                results[filename] = file_path.exists()
            
            return results
        
        # Otherwise, download individual files
        if not self.file_mappings:
            print("⚠️  No Google Drive files configured.")
            print("Set environment variables: GDRIVE_SRD_FOLDER or individual file IDs.")
            return {}
        
        print("📂 Downloading SRD files from Google Drive...\n")
        
        results = {}
        for url_or_id, filename in self.file_mappings.items():
            success = self.download_file(url_or_id, filename, force)
            results[filename] = success
        
        # Summary
        successful = sum(1 for s in results.values() if s)
        total = len(results)
        
        print(f"\n📊 Download Summary: {successful}/{total} files ready")
        
        return results
    
    def verify_files_exist(self, required_files: List[str] = None) -> bool:
        """
        Verify that required files exist in SRD directory.
        
        Args:
            required_files: List of required filenames. If None, checks all configured files.
            
        Returns:
            True if all required files exist
        """
        if required_files is None:
            required_files = list(self.file_mappings.values())
        
        if not required_files:
            # If no files configured, check for default files
            required_files = ["spells.csv", "classes.csv"]
        
        missing = []
        for filename in required_files:
            file_path = self.srd_dir / filename
            if not file_path.exists():
                missing.append(filename)
        
        if missing:
            print(f"⚠️  Missing SRD files: {', '.join(missing)}")
            return False
        
        return True


def download_srd_files(force: bool = False) -> bool:
    """
    Convenience function to download SRD files from Google Drive.
    
    Args:
        force: Force re-download even if files exist
        
    Returns:
        True if all files are ready (downloaded or already exist)
    """
    downloader = GDriveDownloader()
    
    # If no configuration found, just verify existing files
    if not downloader.folder_url and not downloader.file_mappings:
        print("ℹ️  No Google Drive configuration found. Using local files...")
        return downloader.verify_files_exist()
    
    # Download files (folder or individual)
    results = downloader.download_all(force)
    
    # Return True if all downloads succeeded
    return all(results.values()) if results else False


if __name__ == "__main__":
    # Test downloading
    print("Testing Google Drive downloader...")
    download_srd_files(force=False)

