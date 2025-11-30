"""
File handling utilities for document upload and processing.
"""
import os
import logging
import fitz
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'csv'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename, file_type=None):
    """
    Check if file has an allowed extension.

    Args:
        filename: Name of the file
        file_type: Optional specific file type to check (e.g., 'csv')
    """
    if not filename or '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if file_type:
        return ext == file_type.lower()

    return ext in ALLOWED_EXTENSIONS


def save_uploaded_file(file, file_type=None):
    """
    Save uploaded file to temporary location.

    Args:
        file: Flask uploaded file object
        file_type: Optional specific file type to validate (e.g., 'csv')

    Returns:
        str: Path to saved file

    Raises:
        ValueError: If file is invalid
    """
    if not file:
        raise ValueError('No file provided')

    if file.filename == '':
        raise ValueError('No file selected')

    if not allowed_file(file.filename, file_type):
        if file_type:
            raise ValueError(f'Invalid file type. Expected: {file_type.upper()}')
        else:
            raise ValueError('Invalid file type. Allowed: JPG, JPEG, PNG, PDF, CSV')

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return filepath


def convert_pdf_to_png(pdf_filepath):
    """
    Convert PDF to PNG image.

    Args:
        pdf_filepath: Path to PDF file

    Returns:
        str: Path to converted PNG file

    Raises:
        Exception: If conversion fails
    """
    try:
        pdf_document = fitz.open(pdf_filepath)
        page = pdf_document[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        pdf_document.close()

        # Save as PNG
        new_filepath = pdf_filepath.replace('.pdf', '.png')
        with open(new_filepath, 'wb') as f:
            f.write(img_bytes)

        # Remove original PDF
        os.remove(pdf_filepath)

        logger.info(f"Successfully converted PDF to PNG: {new_filepath}")
        return new_filepath

    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        raise


def handle_pdf_conversion(filepath):
    """
    Handle PDF conversion if needed.

    Args:
        filepath: Path to file

    Returns:
        str: Path to file (converted if was PDF)
    """
    if filepath.lower().endswith('.pdf'):
        return convert_pdf_to_png(filepath)
    return filepath


def cleanup_file(filepath):
    """
    Remove temporary file if it exists.

    Args:
        filepath: Path to file to remove
    """
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            logger.info(f"Cleaned up temporary file: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {filepath}: {e}")
