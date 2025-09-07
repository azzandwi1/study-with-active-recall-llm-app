import io
import logging
from pathlib import Path
from typing import Optional, Tuple
import pypdf
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.layout import LAParams
from app.core.settings import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handle PDF text extraction with OCR fallback for low-density pages"""
    
    def __init__(self):
        self.text_density_threshold = settings.text_density_threshold
    
    def extract_text(self, pdf_path: Path) -> Tuple[str, dict]:
        """
        Extract text from PDF with density-based OCR fallback
        
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # First attempt: PyPDF extraction
            text, metadata = self._extract_with_pypdf(pdf_path)
            
            # Check text density
            if self._calculate_text_density(text) < self.text_density_threshold:
                logger.info(f"Low text density detected, falling back to OCR for {pdf_path}")
                # Fallback to OCR
                ocr_text, ocr_metadata = self._extract_with_ocr(pdf_path)
                if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                    metadata.update(ocr_metadata)
                    metadata['extraction_method'] = 'ocr_fallback'
            
            metadata['word_count'] = len(text.split())
            metadata['text_density'] = self._calculate_text_density(text)
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise
    
    def _extract_with_pypdf(self, pdf_path: Path) -> Tuple[str, dict]:
        """Extract text using PyPDF"""
        text_parts = []
        metadata = {
            'extraction_method': 'pypdf',
            'page_count': 0,
            'pages_with_text': 0
        }
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata['page_count'] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(page_text)
                            metadata['pages_with_text'] += 1
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {e}")
                        continue
                
                # Also try PDFMiner as backup for better extraction
                if not text_parts:
                    logger.info("PyPDF failed, trying PDFMiner")
                    pdfminer_text = pdfminer_extract(
                        str(pdf_path),
                        laparams=LAParams(
                            word_margin=0.1,
                            char_margin=2.0,
                            line_margin=0.5,
                            boxes_flow=0.5
                        )
                    )
                    if pdfminer_text.strip():
                        text_parts = [pdfminer_text]
                        metadata['extraction_method'] = 'pdfminer'
                        metadata['pages_with_text'] = 1
        
        except Exception as e:
            logger.error(f"PyPDF extraction failed: {e}")
            raise
        
        return '\n\n'.join(text_parts), metadata
    
    def _extract_with_ocr(self, pdf_path: Path) -> Tuple[str, dict]:
        """Extract text using OCR (PaddleOCR)"""
        try:
            from app.core.ocr import OCRProcessor
            ocr_processor = OCRProcessor()
            return ocr_processor.extract_from_pdf(pdf_path)
        except ImportError:
            logger.warning("OCR not available, skipping OCR extraction")
            return "", {'extraction_method': 'ocr_unavailable'}
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return "", {'extraction_method': 'ocr_failed', 'error': str(e)}
    
    def _calculate_text_density(self, text: str) -> float:
        """
        Calculate text density as ratio of alphanumeric characters to total characters
        
        Returns:
            Float between 0 and 1 representing text density
        """
        if not text:
            return 0.0
        
        alphanumeric_count = sum(1 for c in text if c.isalnum())
        total_count = len(text)
        
        return alphanumeric_count / total_count if total_count > 0 else 0.0
    
    def validate_pdf(self, pdf_path: Path) -> bool:
        """
        Validate PDF file for processing
        
        Returns:
            True if PDF is valid and processable
        """
        try:
            # Check file size
            if pdf_path.stat().st_size > settings.max_upload_bytes:
                logger.error(f"PDF file too large: {pdf_path.stat().st_size} bytes")
                return False
            
            # Check if file is a valid PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                # Check for encryption
                if pdf_reader.is_encrypted:
                    logger.error(f"PDF is encrypted: {pdf_path}")
                    return False
                
                # Check page count
                if len(pdf_reader.pages) == 0:
                    logger.error(f"PDF has no pages: {pdf_path}")
                    return False
                
                # Check for reasonable page count (prevent DoS)
                if len(pdf_reader.pages) > 1000:
                    logger.error(f"PDF has too many pages: {len(pdf_reader.pages)}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"PDF validation failed for {pdf_path}: {e}")
            return False
