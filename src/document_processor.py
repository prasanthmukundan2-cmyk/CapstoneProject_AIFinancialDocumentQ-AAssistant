"""
Document Upload & Processing
Handles file uploads and extracts data for RAG indexing
Supports: PDF, TXT, XLSX (Excel)
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Dict
import PyPDF2
from langchain_core.documents import Document

try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

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
        - XLSX/XLS files (Excel)
        """
        try:
            suffix = file_path.suffix.lower()

            if suffix == ".pdf":
                return self._extract_from_pdf(file_path)
            elif suffix == ".txt":
                return self._extract_from_txt(file_path)
            elif suffix in [".xlsx", ".xls"]:
                if not EXCEL_SUPPORT:
                    raise ValueError("Excel support not available. Install openpyxl: pip install openpyxl")
                return self._extract_from_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {suffix}. Supported: .pdf, .txt, .xlsx, .xls")

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

    def _extract_from_excel(self, file_path: Path) -> str:
        """Extract text from Excel file (XLSX/XLS)"""
        try:
            logger.info(f"Starting Excel extraction from: {file_path}")
            text = ""

            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet_names = workbook.sheetnames
            logger.info(f"Excel file has {len(sheet_names)} sheet(s): {sheet_names}")

            for sheet_name in sheet_names:
                worksheet = workbook[sheet_name]
                text += f"\n{'='*50}\n"
                text += f"Sheet: {sheet_name}\n"
                text += f"{'='*50}\n"

                # Extract headers and data
                for row_num, row in enumerate(worksheet.iter_rows(values_only=True), 1):
                    row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                    text += f"{row_text}\n"

                logger.debug(f"Extracted sheet: {sheet_name}")

            workbook.close()
            logger.info(f"Successfully extracted {len(sheet_names)} sheets from Excel")
            return text

        except Exception as e:
            logger.error(f"Excel extraction error: {type(e).__name__}: {e}")
            raise ValueError(f"Failed to extract Excel file: {str(e)}")

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
