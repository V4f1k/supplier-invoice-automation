"""Surya-OCR service for text extraction from images and PDFs"""

from typing import Union
from pathlib import Path
import tempfile
import os
from loguru import logger
from app.exceptions import OcrError, FileProcessingError

try:
    import fitz  # PyMuPDF for PDF handling
    PYMUPDF_AVAILABLE = True
    logger.info("PyMuPDF available for PDF text extraction")
except ImportError as e:
    logger.warning(f"PyMuPDF not available: {e}")
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from surya.foundation import FoundationPredictor
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    from PIL import Image
    SURYA_AVAILABLE = True
    logger.info("Surya-OCR available for advanced OCR")
except ImportError as e:
    # Surya not available, but we can still use PyMuPDF for basic PDF text extraction
    logger.info(f"Surya-OCR not available, using PyMuPDF for PDF text extraction: {e}")
    FoundationPredictor = None
    RecognitionPredictor = None
    DetectionPredictor = None
    Image = None
    SURYA_AVAILABLE = False


class OCRService:
    """Service for extracting text from images and PDFs using Surya-OCR"""
    
    def __init__(self):
        """Initialize OCR service with model loading"""
        self.foundation_predictor = None
        self.recognition_predictor = None
        self.detection_predictor = None
        self._load_predictors()
    
    def _load_predictors(self) -> None:
        """Load the OCR predictors"""
        if SURYA_AVAILABLE:
            try:
                logger.info("Loading Surya OCR predictors...")
                self.foundation_predictor = FoundationPredictor()
                self.recognition_predictor = RecognitionPredictor(self.foundation_predictor)
                self.detection_predictor = DetectionPredictor()
                logger.info("Surya OCR predictors loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Surya OCR predictors: {e}")
                # Don't raise - fall back to PyMuPDF for PDFs
                self.foundation_predictor = None
                self.recognition_predictor = None
                self.detection_predictor = None
        else:
            logger.info("Surya-OCR not available - using PyMuPDF for PDF text extraction")
            self.foundation_predictor = None
            self.recognition_predictor = None
            self.detection_predictor = None
    
    async def extract_text(self, file_path: Union[str, Path]) -> str:
        """
        Extract text from an image or PDF file
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Extracted text as a string
            
        Raises:
            ValueError: If file format is not supported
            Exception: If OCR processing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}")
        
        # Validate file format first (before mock mode check)
        supported_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
        if file_path.suffix.lower() not in supported_extensions:
            raise FileProcessingError(f"Unsupported file format: {file_path.suffix}")
        
        # Handle PDF files with PyMuPDF if available
        if file_path.suffix.lower() == '.pdf':
            if PYMUPDF_AVAILABLE:
                return await self._extract_from_pdf_simple(file_path)
            else:
                logger.warning("PyMuPDF not available - using mock mode for PDF")
                return f"Mock extracted text from {file_path.name}"
        
        # For images, use Surya if available, otherwise mock mode
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            if SURYA_AVAILABLE and self.recognition_predictor is not None:
                return await self._extract_from_image(file_path)
            else:
                logger.warning("Surya-OCR not available - using mock mode for images")
                return f"Mock extracted text from {file_path.name}"
        
        # This shouldn't be reached due to handling above
        raise FileProcessingError(f"Unsupported file format: {file_path.suffix}")
    
    async def _extract_from_pdf_simple(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF's built-in text extraction"""
        try:
            logger.info(f"Extracting text from PDF using PyMuPDF: {pdf_path}")
            extracted_text = ""
            
            # Open PDF
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text directly from PDF (no OCR needed for text-based PDFs)
                page_text = page.get_text()
                if page_text.strip():
                    extracted_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            
            doc.close()
            
            if not extracted_text.strip():
                logger.warning("No text found in PDF - might be image-based PDF requiring OCR")
                return "No text found in PDF - document may be image-based"
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise OcrError(f"Failed to extract text from PDF: {str(e)}")
    
    async def _extract_from_image(self, image_path: Path) -> str:
        """Extract text from an image file"""
        try:
            # Load image using PIL
            image = Image.open(str(image_path))
            
            # Perform OCR using new Surya API
            predictions = self.recognition_predictor([image], det_predictor=self.detection_predictor)
            
            # Extract text from results
            extracted_text = ""
            for prediction in predictions:
                if hasattr(prediction, 'text_lines'):
                    for line in prediction.text_lines:
                        if hasattr(line, 'text'):
                            extracted_text += line.text + "\n"
                        else:
                            extracted_text += str(line) + "\n"
                elif hasattr(prediction, 'text'):
                    extracted_text += prediction.text + "\n"
                else:
                    # Try to extract text from the prediction structure
                    extracted_text += str(prediction) + "\n"
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from image")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {e}")
            raise OcrError(f"Failed to extract text from image: {str(e)}")
    
    async def _extract_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file by converting pages to images"""
        try:
            extracted_text = ""
            
            # Open PDF
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(img_data)
                    temp_image_path = temp_file.name
                
                try:
                    # Extract text from the page image
                    page_text = await self._extract_from_image(Path(temp_image_path))
                    extracted_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_image_path):
                        os.unlink(temp_image_path)
            
            doc.close()
            logger.info(f"Successfully extracted text from {len(doc)} PDF pages")
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise OcrError(f"Failed to extract text from PDF: {str(e)}")


# Global OCR service instance
_ocr_service = None


async def get_ocr_service() -> OCRService:
    """Get or create the OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


async def extract_text(file_path: Union[str, Path]) -> str:
    """
    Convenience function to extract text from a file
    
    Args:
        file_path: Path to the file to process
        
    Returns:
        Extracted text as a string
    """
    service = await get_ocr_service()
    return await service.extract_text(file_path)