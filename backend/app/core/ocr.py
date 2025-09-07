import logging
from pathlib import Path
from typing import List, Tuple, Dict
import fitz  # PyMuPDF for PDF to image conversion
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handle OCR processing using PaddleOCR"""
    
    def __init__(self):
        self.language = 'en'  # Default to English
        self.confidence_threshold = 0.7
        self._ocr_engine = None
    
    def _get_ocr_engine(self):
        """Lazy initialization of OCR engine"""
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.language,
                    show_log=False
                )
                logger.info("PaddleOCR engine initialized successfully")
            except ImportError:
                logger.error("PaddleOCR not available. Install with: pip install paddlepaddle paddleocr")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {e}")
                raise
        
        return self._ocr_engine
    
    def extract_from_pdf(self, pdf_path: Path) -> Tuple[str, Dict]:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # Convert PDF pages to images
            images = self._pdf_to_images(pdf_path)
            
            if not images:
                return "", {'extraction_method': 'ocr', 'error': 'no_images_extracted'}
            
            # Process each image with OCR
            all_text = []
            ocr_metadata = {
                'extraction_method': 'ocr',
                'pages_processed': 0,
                'total_confidence': 0.0,
                'low_confidence_pages': 0
            }
            
            ocr_engine = self._get_ocr_engine()
            
            for page_num, image in enumerate(images):
                try:
                    page_text, confidence = self._extract_text_from_image(image, ocr_engine)
                    
                    if page_text.strip():
                        all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                        ocr_metadata['pages_processed'] += 1
                        ocr_metadata['total_confidence'] += confidence
                        
                        if confidence < self.confidence_threshold:
                            ocr_metadata['low_confidence_pages'] += 1
                
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num + 1}: {e}")
                    continue
            
            # Calculate average confidence
            if ocr_metadata['pages_processed'] > 0:
                ocr_metadata['average_confidence'] = (
                    ocr_metadata['total_confidence'] / ocr_metadata['pages_processed']
                )
            else:
                ocr_metadata['average_confidence'] = 0.0
            
            extracted_text = '\n\n'.join(all_text)
            return extracted_text, ocr_metadata
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {pdf_path}: {e}")
            return "", {'extraction_method': 'ocr', 'error': str(e)}
    
    def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Images
        """
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(str(pdf_path))
            images = []
            
            for page_num in range(pdf_document.page_count):
                try:
                    # Get page
                    page = pdf_document[page_num]
                    
                    # Convert to image (high DPI for better OCR)
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    images.append(image)
                    
                except Exception as e:
                    logger.warning(f"Failed to convert page {page_num + 1} to image: {e}")
                    continue
            
            pdf_document.close()
            return images
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []
    
    def _extract_text_from_image(self, image: Image.Image, ocr_engine) -> Tuple[str, float]:
        """
        Extract text from a single image using OCR
        
        Args:
            image: PIL Image
            ocr_engine: Initialized PaddleOCR engine
            
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Run OCR
            result = ocr_engine.ocr(img_array, cls=True)
            
            if not result or not result[0]:
                return "", 0.0
            
            # Extract text and confidence scores
            text_parts = []
            confidences = []
            
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]  # Extracted text
                    confidence = line[1][1]  # Confidence score
                    
                    if confidence >= self.confidence_threshold:
                        text_parts.append(text)
                        confidences.append(confidence)
            
            extracted_text = ' '.join(text_parts)
            average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return extracted_text, average_confidence
            
        except Exception as e:
            logger.error(f"OCR processing failed for image: {e}")
            return "", 0.0
    
    def extract_from_image(self, image_path: Path) -> Tuple[str, Dict]:
        """
        Extract text from a single image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # Load image
            image = Image.open(image_path)
            
            # Process with OCR
            ocr_engine = self._get_ocr_engine()
            text, confidence = self._extract_text_from_image(image, ocr_engine)
            
            metadata = {
                'extraction_method': 'ocr',
                'confidence': confidence,
                'image_size': image.size
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"OCR extraction failed for image {image_path}: {e}")
            return "", {'extraction_method': 'ocr', 'error': str(e)}
