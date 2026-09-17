"""
Document Upload & Processing
Handles file uploads and extracts data for RAG indexing
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Dict
import PyPDF2
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process uploaded documents and extract data for RAG"""

    def __init__(self, upload_dir: str = "data/uploaded"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, uploaded_file) -> Path:
        """
        Save uploaded file to disk

        Args:
            uploaded_file: Streamlit UploadedFile object

        Returns:
            Path to saved file
        """
        try:
            file_path = self.upload_dir / uploaded_file.name

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            logger.info(f"Document saved: {uploaded_file.name}")
            return file_path

        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise

    def extract_text_from_file(self, file_path: Path) -> str:
        """
        Extract text from uploaded file

        Supports:
        - PDF files
        - TXT files
        """
        try:
            if file_path.suffix.lower() == ".pdf":
                return self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() == ".txt":
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")

        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            logger.info(f"Starting PDF extraction from: {file_path}")
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {num_pages} pages")

                for page_num in range(num_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text if page_text else "[Page extraction failed]"
                        logger.debug(f"Extracted page {page_num + 1}")
                    except Exception as page_error:
                        logger.warning(f"Error extracting page {page_num + 1}: {page_error}")
                        text += f"\n--- Page {page_num + 1} ---\n[Error extracting this page]\n"

            logger.info(f"Successfully extracted {num_pages} pages from PDF")
            return text

        except Exception as e:
            logger.error(f"PDF extraction error: {type(e).__name__}: {e}")
            raise ValueError(f"Failed to extract PDF: {str(e)}")

    def _extract_from_txt(self, file_path: Path) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            logger.info(f"Extracted text from TXT file")
            return text

        except Exception as e:
            logger.error(f"TXT extraction error: {e}")
            raise

    def process_document(self, uploaded_file) -> Tuple[str, str, Dict]:
        """
        Complete document processing workflow

        1. Save file
        2. Extract text
        3. Create metadata

        Args:
            uploaded_file: Streamlit UploadedFile

        Returns:
            Tuple of (file_path, extracted_text, metadata)
        """
        try:
            # Step 1: Save
            file_path = self.save_uploaded_file(uploaded_file)

            # Step 2: Extract
            text = self.extract_text_from_file(file_path)

            # Step 3: Create metadata
            metadata = {
                "file_name": uploaded_file.name,
                "file_size": uploaded_file.size,
                "file_type": uploaded_file.type,
                "path": str(file_path),
                "text_length": len(text),
            }

            logger.info(f"Document processed: {uploaded_file.name}")
            return str(file_path), text, metadata

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise


# Global instance
_processor = None


def get_document_processor() -> DocumentProcessor:
    """Get or create global document processor"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor


def process_upload(uploaded_file) -> Tuple[str, str, str]:
    """
    Process an uploaded file

    Returns:
        (file_path, text_content, summary)
    """
    processor = get_document_processor()
    return processor.process_document(uploaded_file)
