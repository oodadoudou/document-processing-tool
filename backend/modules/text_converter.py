import os
import re
import logging
from ebooklib import epub
from bs4 import BeautifulSoup
from tqdm import tqdm
import fitz

module_logger = logging.getLogger(__name__)

def epub_to_txt_api(input_dir: str, output_dir: str) -> dict:
    """
    API-adapted: EPUB to TXT conversion.
    Args:
        input_dir (str): The directory containing the EPUB files.
        output_dir (str): The directory where the converted TXT files will be saved.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting EPUB to TXT conversion from '{input_dir}' to '{output_dir}'")
    messages = []
    success_files_details = []
    error_files_details = []
    processed_count = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    try:
        epub_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.epub')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not epub_files:
        msg = f"No EPUB files found in '{input_dir}' for conversion."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "error_count": 0, "success_files": [], "error_files": []}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    total_files = len(epub_files)

    for epub_file in tqdm(epub_files, desc="API EPUB Conversion", unit="file", disable=True):
        input_path = os.path.join(input_dir, epub_file)
        output_filename = f"{os.path.splitext(epub_file)[0]}.txt"
        output_path = os.path.join(output_dir, output_filename)
        processed_count +=1

        try:
            book = epub.read_epub(input_path)
            content_parts = []
            for item in book.get_items():
                if item.get_type() == 9: # ebooklib.ITEM_DOCUMENT
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text_blocks = []
                    for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li']):
                        block_text = elem.get_text(separator=' ', strip=True)
                        if block_text:
                            text_blocks.append(block_text)
                    if text_blocks:
                        content_parts.append('\n'.join(text_blocks))

            full_text_content = '\n\n'.join(content_parts)

            with open(output_path, 'w', encoding='utf-8') as fout:
                fout.write(full_text_content)

            msg = f"Conversion successful: '{epub_file}' -> '{output_filename}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({"original": epub_file, "converted": output_filename})
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            msg = f"Conversion failed for '{epub_file}': {type(e).__name__} - {error_msg}"
            module_logger.error(msg, exc_info=False)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": epub_file, "error": msg})
            error_count += 1
            overall_success = False
    
    final_summary_msg = f"EPUB to TXT conversion finished. Total EPUBs: {total_files}, Succeeded: {len(success_files_details)}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files,
        "success_count": len(success_files_details),
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }


def pdf_to_txt_api(input_dir: str, output_dir: str, output_format: str = 'standard') -> dict:
    """
    API-adapted: PDF to TXT conversion.
    Args:
        input_dir (str): The directory containing the PDF files.
        output_dir (str): The directory where the converted TXT files will be saved.
        output_format (str): Text format ['standard'|'compact'|'clean']
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting PDF to TXT conversion (format: {output_format}) from '{input_dir}' to '{output_dir}'")
    messages = []
    success_files_details = []
    error_files_details = []
    processed_count = 0
    error_count = 0
    overall_success = True

    valid_formats = ['standard', 'compact', 'clean']
    if output_format not in valid_formats:
        msg = f"Invalid output_format: '{output_format}'. Must be one of {valid_formats}."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for conversion."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "error_count": 0, "success_files": [], "error_files": []}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    total_files = len(pdf_files)

    for pdf_file in tqdm(pdf_files, desc="API PDF Conversion", unit="file", disable=True):
        input_path = os.path.join(input_dir, pdf_file)
        output_filename = f"{os.path.splitext(pdf_file)[0]}.txt"
        output_path = os.path.join(output_dir, output_filename)
        processed_count += 1
        text_content = ""

        try:
            with fitz.open(input_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_content += page.get_text("text")
            
            if output_format == 'compact':
                text_content = re.sub(r'\n{3,}', '\n\n', text_content) 
                text_content = re.sub(r'\n{2,}', '\n', text_content) 
            elif output_format == 'clean':
                text_content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\n。，！？、；：“”‘’（）《》〈〉【】「」『』．﹒ :,.!?;\']', '', text_content)
                text_content = re.sub(r'[ \t]{2,}', ' ', text_content)
                text_content = re.sub(r'\n{3,}', '\n\n', text_content)
                text_content = text_content.strip()

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)

            msg = f"Conversion successful: '{pdf_file}' -> '{output_filename}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({"original": pdf_file, "converted": output_filename})
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            msg = f"Conversion failed for '{pdf_file}': {type(e).__name__} - {error_msg}"
            module_logger.error(msg, exc_info=False)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": pdf_file, "error": msg})
            error_count += 1
            overall_success = False

    final_summary_msg = f"PDF to TXT conversion (format: {output_format}) finished. Total PDFs: {total_files}, Succeeded: {len(success_files_details)}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")
    
    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files,
        "success_count": len(success_files_details),
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }