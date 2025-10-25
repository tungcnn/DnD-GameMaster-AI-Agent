"""
SQLite database ingestion for spell data.
Handles database operations, upserts, and spell data management.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.Spell import Spell, Base
from app.models.Class import Class
from ingestion.ingestion_helper import (
    read_spells_csv,
    process_spell_row,
    read_classes_csv,
    process_class_row
)


class SQLiteIngestion:
    def __init__(self, db_path: str = None):
        """
        Initialize SQLite ingestion service.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "resource" / "db" / "checkpoint.db"
        
        self.db_path = str(db_path)
        self._ensure_db_directory()
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def upsert_spell(self, session, **spell_data):
        """
        Upsert a spell record into the database.
        
        Args:
            session: SQLAlchemy session
            **spell_data: Spell data (name, cast_class, description, effect_kind, damage, heal)
        """
        stmt = sqlite_insert(Spell).values(**spell_data).on_conflict_do_update(
            index_elements=[Spell.name],  # conflict target
            set_={
                "cast_class": spell_data.get("cast_class"),
                "description": spell_data.get("description"),
                "effect_kind": spell_data.get("effect_kind"),
                "damage": spell_data.get("damage"),
                "heal": spell_data.get("heal"),
            },
        )
        session.execute(stmt)
    
    def upsert_class(self, session, **class_data):
        """
        Upsert a class record into the database.
        
        Args:
            session: SQLAlchemy session
            **class_data: Class data (name, index, health)
        """
        stmt = sqlite_insert(Class).values(**class_data).on_conflict_do_update(
            index_elements=[Class.name],  # conflict target
            set_={
                "index": class_data.get("index"),
                "health": class_data.get("health"),
            },
        )
        session.execute(stmt)
    
    def ingest_spells_from_csv(
        self, 
        csv_path: str, 
        batch_size: int = 100,
        slot_level: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ingest spells from CSV file into SQLite database.
        
        Args:
            csv_path: Path to CSV file containing spell data
            batch_size: Number of records to process before committing
            slot_level: Spell slot level for damage/heal calculations
            
        Returns:
            List of processed spell data dictionaries for embedding generation
        """
        session = self.Session()
        spells_for_embeddings = []
        
        try:
            # Read CSV file using helper
            df = read_spells_csv(csv_path)
            print(f"Loaded {len(df)} rows. Preparing data...")

            processed_count = 0
            
            for _, row in df.iterrows():
                # Process row using helper function
                spell_data = process_spell_row(row, slot_level=slot_level)
                
                if not spell_data:
                    continue

                # Upsert spell to database
                self.upsert_spell(session, **spell_data)
                
                # Collect spell data for embeddings
                spells_for_embeddings.append(spell_data)
                
                processed_count += 1

                # Commit in batches for better performance
                if processed_count % batch_size == 0:
                    session.commit()
                    print(f"Processed {processed_count} spells...")

            # Final commit for remaining records
            session.commit()
            print(f"Successfully processed {processed_count} spells into database.")
            
            return spells_for_embeddings

        except Exception as e:
            session.rollback()
            print(f"Error during SQLite ingestion: {e}")
            raise
        finally:
            session.close()
    
    def ingest_classes_from_csv(
        self, 
        csv_path: str, 
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Ingest classes from CSV file into SQLite database.
        
        Args:
            csv_path: Path to CSV file containing class data
            batch_size: Number of records to process before committing
            
        Returns:
            List of processed class data dictionaries
        """
        session = self.Session()
        classes_data = []
        
        try:
            # Read CSV file using helper
            df = read_classes_csv(csv_path)
            print(f"Loaded {len(df)} class rows. Preparing data...")

            processed_count = 0
            
            for _, row in df.iterrows():
                # Process row using helper function
                class_data = process_class_row(row)
                
                if not class_data:
                    continue

                # Upsert class to database
                self.upsert_class(session, **class_data)
                
                # Collect class data for return
                classes_data.append(class_data)
                
                processed_count += 1

                # Commit in batches for better performance
                if processed_count % batch_size == 0:
                    session.commit()
                    print(f"Processed {processed_count} classes...")

            # Final commit for remaining records
            session.commit()
            print(f"Successfully processed {processed_count} classes into database.")
            
            return classes_data

        except Exception as e:
            session.rollback()
            print(f"Error during SQLite ingestion: {e}")
            raise
        finally:
            session.close()
    
    def get_all_spells(self) -> List[Spell]:
        """
        Get all spells from the database.
        
        Returns:
            List of Spell objects
        """
        session = self.Session()
        try:
            return session.query(Spell).all()
        finally:
            session.close()
    
    def get_all_classes(self) -> List[Class]:
        """
        Get all classes from the database.
        
        Returns:
            List of Class objects
        """
        session = self.Session()
        try:
            return session.query(Class).all()
        finally:
            session.close()
    
    def get_spell_by_name(self, name: str) -> Spell:
        """
        Get a specific spell by name.
        
        Args:
            name: Spell name
            
        Returns:
            Spell object or None
        """
        session = self.Session()
        try:
            return session.query(Spell).filter(Spell.name == name).first()
        finally:
            session.close()
    
    def search_spells(
        self, 
        name: str = None, 
        cast_class: str = None,
        effect_kind: str = None
    ) -> List[Spell]:
        """
        Search spells with filters.
        
        Args:
            name: Filter by spell name (partial match)
            cast_class: Filter by casting class
            effect_kind: Filter by effect type (damage, heal, none)
            
        Returns:
            List of matching Spell objects
        """
        session = self.Session()
        try:
            query = session.query(Spell)
            
            if name:
                query = query.filter(Spell.name.like(f"%{name}%"))
            if cast_class:
                query = query.filter(Spell.cast_class.like(f"%{cast_class}%"))
            if effect_kind:
                query = query.filter(Spell.effect_kind == effect_kind)
            
            return query.all()
        finally:
            session.close()
    
    def get_session(self):
        """Get a new database session."""
        return self.Session()
    
    def close(self):
        """Close the database engine."""
        self.engine.dispose()


# Create a global instance
sqlite_ingestion = SQLiteIngestion()
