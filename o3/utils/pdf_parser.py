import PyPDF2
import logging
from pdf2image import convert_from_bytes
import pytesseract
from io import BytesIO

"""
Utility class for parsing text from PDF documents with OCR fallback.
Extracts text from PDFs for local analysis.

file path: utils/pdf_parser.py
"""

logger = logging.getLogger(__name__)

class DocumentParser:
    """
    Utility class for parsing text from PDF documents with OCR fallback.
    """
    def parse_document(self, pdf_files: list) -> list[str]:
        """
        Extract text from a list of PDF files, falling back to OCR if necessary.

        Args:
            pdf_files (list): List of file-like objects (e.g., opened in 'rb' mode).

        Returns:
            list[str]: List of text extracted from each page; empty string for unreadable pages,
                       or ["No readable content"] if all pages fail.
        """
        pages = []
        for pdf_file in pdf_files:
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            try:
                pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text() or ""
                    if text.strip() and len(text) > 50:
                        pages.append(text)
                    else:
                        logger.warning(f"No text from PyPDF2 on page {page_num}, trying OCR")
                        images = convert_from_bytes(pdf_bytes, first_page=page_num + 1, last_page=page_num + 1)
                        if images:
                            ocr_text = pytesseract.image_to_string(images[0]).strip()
                            if ocr_text and len(ocr_text) > 50:
                                pages.append(ocr_text)
                            else:
                                pages.append("")
                        else:
                            pages.append("")
            except Exception as e:
                logger.error(f"PyPDF2 failed: {str(e)}, falling back to OCR")
                try:
                    images = convert_from_bytes(pdf_bytes)
                    for img in images:
                        ocr_text = pytesseract.image_to_string(img).strip()
                        if ocr_text and len(ocr_text) > 50:
                            pages.append(ocr_text)
                        else:
                            pages.append("")
                except Exception as e:
                    logger.error(f"OCR failed: {str(e)}")
                    pages.append("")
        return pages if pages else ["No readable content"]

    def preprocess_ocr(self, text: str) -> str:
        """
        Preprocess OCR-extracted text to clean it up.

        Args:
            text (str): Raw text from OCR.

        Returns:
            str: Cleaned text with normalized whitespace.
        """
        return ' '.join(text.strip().split())

    def split_into_chunks(self, text: str, chunk_size: int = 4096) -> list[str]:
        """
        Split a large text string into smaller chunks.

        Args:
            text (str): Text to split.
            chunk_size (int): Size of each chunk (default 4096 characters).

        Returns:
            list[str]: List of text chunks; ["Empty chunk"] if text is empty.
        """
        if not text or not text.strip():
            return ["Empty chunk"]
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    def ocr_image(self, image) -> str:
        """
        Perform OCR on a single image.

        Args:
            image: Image object to process.

        Returns:
            str: Extracted text from the image.
        """
        try:
            text = pytesseract.image_to_string(image).strip()
            return self.preprocess_ocr(text)
        except Exception as e:
            logger.error(f"OCR failed on image: {str(e)}")
            return ""