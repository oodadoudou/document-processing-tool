import os
import time
import logging
import fitz
from tqdm import tqdm
import pikepdf
from pathlib import Path
import shutil

try:
    from modules import report_generator
except ImportError:
    import report_generator

logger = logging.getLogger(__name__)

def remove_pdf_pages(input_dir: str, output_dir: str, trim_type: str = 'f', num_pages: int = 1) -> None:
    """
    PDF Page Cropping Function (Ultimate Stable Version)
    Removes pages from the beginning or end of PDF files by rebuilding the document structure.
    Args:
        input_dir (str): The directory containing the PDF files to process.
        output_dir (str): The directory where the processed PDF files will be saved.
        trim_type (str): Type of trimming ('f' for first N pages, 'l' for last N pages, 'lf' for first and last page).
        num_pages (int): Number of pages to trim from front or back (default 1).
    """
    success_files = []
    error_files = []
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.warning(f"No PDF files found in '{input_dir}' for page trimming.")
        return

    for pdf_file in tqdm(pdf_files, desc="PDF Page Trimming"):
        input_path = os.path.join(input_dir, pdf_file)
        output_path = os.path.join(output_dir, pdf_file)

        try:
            with fitz.open(input_path) as src_doc:
                new_doc = fitz.open()
                new_doc.set_metadata(src_doc.metadata)
                new_doc.set_toc(src_doc.get_toc())

                keep_pages = []
                if trim_type == 'f':
                    keep_pages = list(range(num_pages, len(src_doc)))
                elif trim_type == 'l':
                    keep_pages = list(range(0, len(src_doc) - num_pages))
                elif trim_type == 'lf':
                    keep_pages = list(range(1, len(src_doc) - 1))
                else:
                    raise ValueError(f"Invalid trim type: {trim_type}")

                for pg_num in keep_pages:
                    page = src_doc.load_page(pg_num)
                    new_page = new_doc.new_page(-1, width=page.rect.width, height=page.rect.height)
                    new_page.show_pdf_page(
                        page.rect,
                        src_doc,
                        pg_num,
                        keep_proportion=True
                    )

                new_doc.save(
                    output_path,
                    garbage=4,
                    deflate=True,
                    clean=True,
                    linear=True,
                    no_new_id=True,
                )

                success_files.append(pdf_file)
                logger.info(f"Deep rebuild successful: {pdf_file} ({len(src_doc)}→{len(new_doc)} pages). Saved to: {output_path}")

        except Exception as e:
            error_msg = str(e).split('\n')[0]
            error_files.append((pdf_file, error_msg))
            logger.error(f"Structure rebuild failed | {pdf_file} | Error: {error_msg}")

            if os.path.exists(output_path):
                try: os.remove(output_path)
                except: pass

    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="PDF Page Trimming Report",
        total_processed=len(success_files) + len(error_files),
        success_files=success_files,
        error_files=error_files,
        duration=duration
    )


def remove_specific_pages_from_pdf(file_path: Path, pages_to_delete: list) -> bool:
    """
    Removes specific pages from a PDF file using pikepdf and overwrites the original file.
    It's assumed that the input PDF is not encrypted or has been decrypted beforehand.
    Args:
        file_path (Path): The path to the PDF file.
        pages_to_delete (list): A list of 0-indexed page numbers to delete.
                                 e.g., [0, 2, 4] to delete the 1st, 3rd, and 5th pages.
    Returns:
        bool: True if pages were successfully removed, False otherwise.
    """
    if not file_path.exists() or not file_path.is_file() or file_path.suffix.lower() != '.pdf':
        logger.error(f"Error: Invalid PDF file path provided: {file_path}")
        return False

    temp_file = file_path.with_suffix('.tmp.pdf')

    try:
        with pikepdf.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            valid_pages_to_delete = sorted(list(set(p for p in pages_to_delete if 0 <= p < total_pages)), reverse=True)

            if not valid_pages_to_delete:
                logger.info(f"No valid pages to delete from {file_path.name}. Skipping.")
                return True

            for page_num in valid_pages_to_delete:
                del pdf.pages[page_num]

            pdf.save(temp_file)
            os.replace(temp_file, file_path)
            logger.info(f"Successfully removed pages {sorted([p+1 for p in valid_pages_to_delete])} from {file_path.name}")
            return True
    except pikepdf.PasswordError:
        logger.error(f"Error: PDF '{file_path.name}' is encrypted. Please decrypt it first.")
        return False
    except Exception as e:
        logger.error(f"Failed to remove pages from '{file_path.name}': {type(e).__name__} - {e}")
        return False
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError as e:
                logger.warning(f"Could not delete temporary file {temp_file}: {e}")

def process_pdfs_for_specific_page_removal_in_directory(directory_path: Path, pages_to_delete: list, output_dir: Path) -> None:
    """
    Iterates through all PDF files in a given directory and removes specific pages from each.
    Processed PDFs are saved to the specified output directory.
    Args:
        directory_path (Path): The directory containing the PDF files to process.
        pages_to_delete (list): A list of 0-indexed page numbers to delete from each PDF.
        output_dir (Path): The directory where the processed PDF files will be saved.
    """
    if not directory_path.is_dir():
        logger.error(f"Error: Directory not found: {directory_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    pdf_files_in_dir = list(directory_path.glob("*.pdf"))

    if not pdf_files_in_dir:
        logger.warning(f"No PDF files found in '{directory_path}'.")
        return

    logger.info(f"Starting to remove specific pages ({[p+1 for p in pages_to_delete]} as 1-indexed) from PDFs in: {directory_path}")
    
    processed_count = 0
    failed_files = []
    start_time = time.time()

    for pdf_file_path in tqdm(pdf_files_in_dir, desc="Processing PDFs for specific page removal"):
        output_file_path = output_dir / pdf_file_path.name
        
        try:
            if pdf_file_path.resolve() != output_file_path.resolve():
                import shutil
                shutil.copy2(pdf_file_path, output_file_path)
        except Exception as e:
            logger.error(f"Failed to copy '{pdf_file_path.name}' to output directory: {e}")
            failed_files.append((pdf_file_path.name, f"Copy failed: {e}"))
            continue

        logger.info(f"Processing file: {output_file_path.name}")
        success = remove_specific_pages_from_pdf(output_file_path, pages_to_delete)
        if success:
            processed_count += 1
        else:
            failed_files.append((pdf_file_path.name, "Page removal failed"))

    logger.info("Specific page removal batch complete.")
    report_generator.generate_report(
        report_title="Specific PDF Page Removal Report",
        total_processed=len(pdf_files_in_dir),
        success_files=[f[0] for f in failed_files if f[1] != "Page removal failed"] if failed_files else [f.name for f in pdf_files_in_dir],
        error_files=failed_files,
        duration=time.time() - start_time
    )


def repair_pdfs_by_rebuilding(input_dir: str, output_dir: str) -> bool:
    """
    Attempts to repair PDF internal structure by re-saving.
    This helps resolve issues caused by PDF file corruption or format problems during merging.
    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str): Directory to save repaired PDFs.
    Returns:
        bool: True if all files were successfully repaired, False otherwise.
    """
    logger.info(f"Starting PDF file structure repair (by re-saving)...")

    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.warning("No PDF files found for repair.")
        return True

    success_files = []
    error_files = []
    start_time = time.time()

    with tqdm(pdf_files, desc="Repairing PDFs") as pbar:
        for filename in pbar:
            input_path = os.path.join(input_dir, filename)
            temp_output_path = os.path.join(input_dir, f"~temp_repaired_{filename}")
            final_output_path = os.path.join(output_dir, filename)

            try:
                with pikepdf.open(input_path) as pdf:
                    pdf.save(temp_output_path)

                shutil.move(temp_output_path, final_output_path)

                success_files.append(filename)
                logger.info(f"Repair successful: {filename}. Saved to: {final_output_path}")
            except Exception as e:
                error_files.append((filename, str(e)))
                logger.error(f"Repair failed: {filename} - {str(e)}")
            finally:
                if os.path.exists(temp_output_path):
                    try:
                        os.remove(temp_output_path)
                    except OSError as e:
                        logger.warning(f"Could not delete temporary file {temp_output_path}: {e}")

    report_generator.generate_report(
        report_title="PDF Repair Report",
        total_processed=len(pdf_files),
        success_files=success_files,
        error_files=error_files,
        duration=time.time() - start_time
    )
    return len(error_files) == 0