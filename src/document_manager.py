"""
Enhanced Document Manager
Handles document upload, indexing, and management
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from rag.vector_store import FinancialVectorStore
from rag.document_loader import FinancialDocumentLoader
from rag.text_splitter import FinancialTextSplitter
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentManager:
    """Manages document uploads, indexing, and metadata."""

    def __init__(self, upload_dir: str = "data/uploaded"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.upload_dir / "metadata.json"
        self.vector_store = FinancialVectorStore(db_dir="vector_db")
        self.document_loader = FinancialDocumentLoader()
        self.text_splitter = FinancialTextSplitter()
        self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load existing metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
        return self.metadata

    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")

    def upload_document(self, file_path: str, file_name: str) -> Dict:
        """
        Upload and index a document.

        Args:
            file_path: Path to the file to upload
            file_name: Original file name

        Returns:
            Document metadata
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Save file to upload directory
            dest_path = self.upload_dir / file_name
            with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

            # Create metadata
            file_size = dest_path.stat().st_size
            metadata = {
                "name": file_name,
                "path": str(dest_path),
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024*1024), 2),
                "upload_time": datetime.now().isoformat(),
                "indexed": False,
                "indexed_time": None,
                "chunks": 0,
            }

            # Store metadata
            self.metadata[file_name] = metadata
            self._save_metadata()

            logger.info(f"Document uploaded: {file_name} ({file_size} bytes)")
            return metadata

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise

    def index_document(self, file_name: str) -> Dict:
        """
        Index a document in the vector store.

        Args:
            file_name: Name of the document to index

        Returns:
            Updated metadata with indexing info
        """
        try:
            if file_name not in self.metadata:
                raise ValueError(f"Document not found in metadata: {file_name}")

            file_path = self.metadata[file_name]["path"]

            # Load document
            documents = self.document_loader.load_documents([file_path])
            if not documents:
                raise ValueError(f"No documents loaded from {file_name}")

            # Split text
            chunks = self.text_splitter.split_documents(documents)

            # Index in vector store
            self.vector_store.index_documents(chunks, doc_name=file_name)

            # Update metadata
            self.metadata[file_name]["indexed"] = True
            self.metadata[file_name]["indexed_time"] = datetime.now().isoformat()
            self.metadata[file_name]["chunks"] = len(chunks)
            self._save_metadata()

            logger.info(f"Document indexed: {file_name} ({len(chunks)} chunks)")
            return self.metadata[file_name]

        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

    def index_all_documents(self) -> List[Dict]:
        """
        Index all uploaded documents.

        Returns:
            List of metadata for indexed documents
        """
        results = []
        for file_name in self.metadata:
            if not self.metadata[file_name].get("indexed", False):
                try:
                    result = self.index_document(file_name)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to index {file_name}: {e}")

        return results

    def get_document_info(self, file_name: str) -> Optional[Dict]:
        """Get metadata for a specific document."""
        return self.metadata.get(file_name)

    def get_all_documents(self) -> List[Dict]:
        """Get all documents with metadata."""
        return list(self.metadata.values())

    def delete_document(self, file_name: str) -> bool:
        """
        Delete a document.

        Args:
            file_name: Name of the document to delete

        Returns:
            True if successful
        """
        try:
            if file_name not in self.metadata:
                raise ValueError(f"Document not found: {file_name}")

            file_path = Path(self.metadata[file_name]["path"])
            if file_path.exists():
                file_path.unlink()

            del self.metadata[file_name]
            self._save_metadata()

            logger.info(f"Document deleted: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Get statistics about uploaded documents."""
        total_size = sum(doc.get("size_bytes", 0) for doc in self.metadata.values())
        indexed_count = sum(1 for doc in self.metadata.values() if doc.get("indexed", False))
        total_chunks = sum(doc.get("chunks", 0) for doc in self.metadata.values())

        return {
            "total_documents": len(self.metadata),
            "indexed_documents": indexed_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "total_chunks": total_chunks,
            "avg_chunks_per_doc": round(total_chunks / len(self.metadata), 1) if self.metadata else 0,
        }
