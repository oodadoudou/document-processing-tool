import os
import re
import logging
import time
from ebooklib import epub
from bs4 import BeautifulSoup
from tqdm import tqdm
import fitz

try:
    from modules import report_generator
except ImportError:
    import report_generator

logger = logging.getLogger(__name__)

def epub_to_txt(input_dir: str, output_dir: str) -> None:
    """
    EPUB to TXT conversion.
    Processing logic:
        1. Parses EPUB directory structure.
        2. Extracts text content (retains paragraph structure).
        3. Filters HTML tags.
        4. Adds source annotation.
    Dependencies:
        - ebooklib for parsing EPUB.
        - BeautifulSoup for processing HTML.
    Output:
        Generates a .txt file with the same name, containing cleaned text content.
    Args:
        input_dir (str): The directory containing the EPUB files.
        output_dir (str): The directory where the converted TXT files will be saved.
    """
    logger.info("Starting batch EPUB to TXT conversion")
    epub_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.epub')]

    if not epub_files:
        logger.warning(f"No EPUB files found in '{input_dir}' for conversion.")
        return

    os.makedirs(output_dir, exist_ok=True)

    success_files = []
    error_files = []
    start_time = time.time()

    for epub_file in tqdm(epub_files, desc="EPUB Conversion"):
        try:
            input_path = os.path.join(input_dir, epub_file)
            output_path = os.path.join(output_dir, f"{os.path.splitext(epub_file)[0]}.txt")

            book = epub.read_epub(input_path)

            content = []
            for item in book.get_items():
                if item.get_type() == 9: # Check if it's a document (html/xhtml)
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text_blocks = [
                        elem.get_text(strip=True)
                        for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'div'])
                        if elem.get_text(strip=True)
                    ]
                    content.append('\n\n'.join(text_blocks))

            with open(output_path, 'w', encoding='utf-8') as fout:
                fout.write('\n\n'.join(content))

            logger.info(f"✅ Conversion successful: {epub_file} → {os.path.basename(output_path)}")
            success_files.append(epub_file)
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            logger.error(f"Conversion failed for {epub_file}: {type(e).__name__} - {error_msg}")
            error_files.append((epub_file, error_msg))

    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="EPUB to TXT Conversion Report",
        total_processed=len(epub_files),
        success_files=success_files,
        error_files=error_files,
        duration=duration
    )


def pdf_to_txt(input_dir: str, output_dir: str, output_format: str = 'standard') -> None:
    """
    PDF to TXT conversion.
    Args:
        input_dir (str): The directory containing the PDF files.
        output_dir (str): The directory where the converted TXT files will be saved.
        output_format (str): Text format [standard|compact|clean]
            standard : Retains original format (default).
            compact  : Compact mode, reduces blank lines.
            clean    : Clean mode, removes non-text content.
    """
    logger.info(f"Starting batch PDF to TXT conversion (format: {output_format})")
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.warning(f"No PDF files found in '{input_dir}' for conversion.")
        return

    os.makedirs(output_dir, exist_ok=True)

    success_files = []
    error_files = []
    start_time = time.time()

    for pdf_file in tqdm(pdf_files, desc="PDF Conversion"):
        try:
            input_path = os.path.join(input_dir, pdf_file)
            output_path = os.path.join(output_dir, f"{os.path.splitext(pdf_file)[0]}.txt")

            text = ""
            with fitz.open(input_path) as doc:
                for page in doc:
                    text += page.get_text()

            if output_format == 'compact':
                text = re.sub(r'\n{3,}', '\n', text) # Reduce multiple newlines to single
            elif output_format == 'clean':
                # Remove non-text characters and reduce multiple spaces
                text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s。，！？.,:;]', '', text)
                text = re.sub(r'\s+', ' ', text).strip() # Reduce multiple spaces to single and strip leading/trailing

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            logger.info(f"✅ Conversion successful: {pdf_file} → {os.path.basename(output_path)}")
            success_files.append(pdf_file)
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            logger.error(f"Conversion failed for {pdf_file}: {type(e).__name__} - {error_msg}")
            error_files.append((pdf_file, error_msg))

    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="PDF to TXT Conversion Report",
        total_processed=len(pdf_files),
        success_files=success_files,
        error_files=error_files,
        duration=duration
    )