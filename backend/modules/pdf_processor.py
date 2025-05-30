# backend/modules/pdf_processor.py
import os
import time
import logging
import shutil
from pathlib import Path
import fitz # PyMuPDF
import pikepdf
from tqdm import tqdm

module_logger = logging.getLogger(__name__)

def remove_pdf_pages_api(input_dir: str, output_dir: str, trim_type: str = 'f', num_pages: int = 1) -> dict:
    """
    API-adapted: PDF Page Cropping Function.
    Removes pages from the beginning or end of PDF files by rebuilding the document structure.
    Args:
        input_dir (str): The directory containing the PDF files to process.
        output_dir (str): The directory where the processed PDF files will be saved.
        trim_type (str): Type of trimming ('f', 'l', 'lf').
        num_pages (int): Number of pages to trim.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting PDF page trimming (type: {trim_type}, pages: {num_pages}) from '{input_dir}' to '{output_dir}'.")
    messages = []
    success_files_details = []  # List of {"original": "file.pdf", "processed": "file.pdf", "original_pages": X, "new_pages": Y}
    error_files_details = []    # List of {"file": "file.pdf", "error": "error message"}
    processed_count = 0 # Counts files attempted
    success_count = 0
    error_count = 0
    overall_success = True

    valid_trim_types = ['f', 'l', 'lf']
    if trim_type not in valid_trim_types:
        msg = f"Invalid trim_type: '{trim_type}'. Must be one of {valid_trim_types}."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    if not isinstance(num_pages, int) or num_pages < 0: # num_pages can be 0 if no trimming is desired for a type
        msg = f"Invalid num_pages: '{num_pages}'. Must be a non-negative integer."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}


    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for page trimming."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    total_files_to_process = len(pdf_files)

    for pdf_file in tqdm(pdf_files, desc="API PDF Page Trimming", unit="file", disable=True):
        input_path = os.path.join(input_dir, pdf_file)
        output_path = os.path.join(output_dir, pdf_file) # Output has the same name in the output_dir
        processed_count +=1
        original_page_count = 0
        new_page_count = 0

        try:
            with fitz.open(input_path) as src_doc:
                original_page_count = len(src_doc)
                if original_page_count == 0:
                    msg = f"Skipping '{pdf_file}': PDF has no pages."
                    module_logger.warning(msg)
                    messages.append(f"[WARN] {msg}")
                    error_files_details.append({"file": pdf_file, "error": "PDF has no pages"})
                    error_count +=1 # Consider this a file-specific error/skip
                    continue

                new_doc = fitz.open() # Create a new PDF
                new_doc.set_metadata(src_doc.metadata) # Copy metadata
                # TOC copying can be complex and error-prone, do it carefully
                try:
                    toc = src_doc.get_toc(simple=False) # Get full ToC
                    if toc:
                        new_doc.set_toc(toc)
                except Exception as e_toc:
                    module_logger.warning(f"Could not copy ToC for '{pdf_file}': {e_toc}")
                    messages.append(f"[WARN] Could not copy ToC for '{pdf_file}': {e_toc}")


                pages_to_keep_indices = []
                if trim_type == 'f':
                    # Keep pages from num_pages to the end
                    start_index = num_pages
                    if start_index >= original_page_count: # Trying to remove all or more pages
                        pages_to_keep_indices = []
                    else:
                        pages_to_keep_indices = list(range(start_index, original_page_count))
                elif trim_type == 'l':
                    # Keep pages from 0 up to (total - num_pages -1)
                    end_index = original_page_count - num_pages
                    if end_index <= 0: # Trying to remove all or more pages
                        pages_to_keep_indices = []
                    else:
                        pages_to_keep_indices = list(range(0, end_index))
                elif trim_type == 'lf':
                    # Keep pages from 1 to (total - 2)
                    if original_page_count <= 2: # If 0, 1 or 2 pages, removing 1st and last results in 0 pages
                        pages_to_keep_indices = []
                    else:
                        pages_to_keep_indices = list(range(1, original_page_count - 1))
                
                if not pages_to_keep_indices and original_page_count > 0 : # All pages are trimmed
                    msg = f"All pages trimmed for '{pdf_file}'. Original: {original_page_count} pages."
                    module_logger.info(msg)
                    # Save an empty PDF or a PDF with one blank page?
                    # For now, saving an empty PDF if all pages are trimmed.
                    new_doc.save(output_path, garbage=4, deflate=True, clean=True)
                    new_page_count = 0

                elif pages_to_keep_indices:
                    # new_doc.insert_pdf(src_doc, from_page=pages_to_keep_indices[0], to_page=pages_to_keep_indices[-1], start_at=-1)
                    # Using show_pdf_page for potentially better handling of complex pages
                    for pg_num_to_keep in pages_to_keep_indices:
                        page = src_doc.load_page(pg_num_to_keep)
                        # Create new page in new_doc with same dimensions
                        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                        # Show original page content on the new page
                        new_page.show_pdf_page(page.rect, src_doc, pg_num_to_keep)
                    
                    new_doc.save(output_path, garbage=4, deflate=True, clean=True, linear=True, no_new_id=True)
                    new_page_count = len(new_doc)
                else: # No pages to keep and original was empty
                     new_doc.save(output_path, garbage=4, deflate=True, clean=True)
                     new_page_count = 0


            msg = f"Page trimming successful for '{pdf_file}'. Original: {original_page_count}, New: {new_page_count}. Saved to '{output_path}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({
                "original": pdf_file, 
                "processed": os.path.basename(output_path), 
                "original_pages": original_page_count, 
                "new_pages": new_page_count
            })
            success_count += 1

        except ValueError as ve: # For invalid trim_type if not caught earlier
            error_msg = str(ve)
            msg = f"Configuration error for '{pdf_file}': {error_msg}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": pdf_file, "error": msg})
            error_count += 1
            overall_success = False
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            msg = f"Page trimming failed for '{pdf_file}': {type(e).__name__} - {error_msg}"
            module_logger.error(msg, exc_info=False)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": pdf_file, "error": msg})
            error_count += 1
            overall_success = False
            if os.path.exists(output_path): # Clean up partially created file
                try: os.remove(output_path)
                except Exception: pass
    
    final_summary_msg = f"PDF page trimming finished. Total PDFs: {total_files_to_process}, Succeeded: {success_count}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files_to_process,
        "success_count": success_count,
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }


def _remove_specific_pages_from_single_pdf_for_api(file_path: Path, pages_to_delete: list, module_logger_ref: logging.Logger) -> tuple[bool, str, int, int]:
    """
    Internal helper: Removes specific pages from a single PDF.
    Returns: (success_flag, message, original_page_count, final_page_count)
    """
    original_page_count = 0
    final_page_count = 0
    
    if not file_path.exists() or not file_path.is_file() or file_path.suffix.lower() != '.pdf':
        return False, f"Invalid PDF file path: {file_path}", 0, 0

    # Use a temporary file in the same directory as the target file
    temp_file = file_path.with_name(f"~tmp_{file_path.name}")

    try:
        with pikepdf.open(file_path) as pdf:
            original_page_count = len(pdf.pages)
            # Filter and sort pages to delete: must be valid 0-indexed, delete from highest to lowest to avoid index shifts
            valid_pages_to_delete = sorted(list(set(p for p in pages_to_delete if 0 <= p < original_page_count)), reverse=True)

            if not valid_pages_to_delete:
                final_page_count = original_page_count
                return True, f"No valid pages to delete from '{file_path.name}'. Original pages: {original_page_count}.", original_page_count, final_page_count
            
            pages_deleted_log = sorted([p+1 for p in valid_pages_to_delete]) # For logging 1-indexed

            for page_num_idx in valid_pages_to_delete:
                del pdf.pages[page_num_idx]
            
            final_page_count = len(pdf.pages)
            pdf.save(temp_file) # Save changes to temporary file
        
        # Replace original file with temporary file
        shutil.move(str(temp_file), str(file_path)) # Use shutil.move for robustness
        return True, f"Successfully removed pages {pages_deleted_log} from '{file_path.name}'. Original: {original_page_count}, Final: {final_page_count}.", original_page_count, final_page_count
    
    except pikepdf.PasswordError:
        return False, f"PDF '{file_path.name}' is encrypted. Please decrypt it first.", original_page_count, original_page_count
    except Exception as e:
        return False, f"Failed to remove pages from '{file_path.name}': {type(e).__name__} - {str(e).splitlines()[0]}", original_page_count, original_page_count
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError as e_os:
                module_logger_ref.warning(f"Could not delete temporary file '{temp_file}': {e_os}")


def process_pdfs_for_specific_page_removal_api(input_dir: str, output_dir: str, pages_to_delete_str: str) -> dict:
    """
    API-adapted: Iterates through PDFs in input_dir, removes specific pages, saves to output_dir.
    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str): Directory to save processed PDFs.
        pages_to_delete_str (str): Space-separated string of 0-indexed page numbers.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Removing specific pages '{pages_to_delete_str}' from PDFs in '{input_dir}', output to '{output_dir}'.")
    messages = []
    success_files_details = []
    error_files_details = []
    processed_count = 0
    success_count = 0
    error_count = 0
    overall_success = True

    try:
        pages_to_delete = [int(p.strip()) for p in pages_to_delete_str.split()]
        if not all(p >= 0 for p in pages_to_delete):
            raise ValueError("Page numbers must be non-negative integers.")
    except ValueError:
        msg = "Invalid page numbers string. Must be space-separated non-negative integers."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}'."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    total_files_to_process = len(pdf_files)

    for filename in tqdm(pdf_files, desc="API Removing Specific Pages", unit="file", disable=True):
        input_file_path = Path(input_dir) / filename
        output_file_path = Path(output_dir) / filename # Processed file will have same name in output_dir
        processed_count += 1
        
        # 1. Copy file to output directory first
        try:
            if input_file_path.resolve() != output_file_path.resolve(): # Avoid copying if input and output are same file
                 shutil.copy2(str(input_file_path), str(output_file_path))
            # If they are the same, the operation will be in-place on the file in output_dir (which is also input_dir)
        except Exception as e_copy:
            msg = f"Failed to copy '{filename}' to output directory '{output_dir}': {e_copy}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": filename, "error": f"Copy to output failed: {e_copy}"})
            error_count += 1
            overall_success = False
            continue # Skip processing this file

        # 2. Process the file in the output directory
        file_processed_successfully, process_message, orig_pg, final_pg = _remove_specific_pages_from_single_pdf_for_api(output_file_path, pages_to_delete, module_logger)
        
        if file_processed_successfully:
            messages.append(f"[SUCCESS] {process_message}")
            success_files_details.append({
                "file": filename, 
                "original_pages": orig_pg,
                "final_pages": final_pg,
                "removed_pages_specified": sorted([p+1 for p in pages_to_delete if 0 <= p < orig_pg])
            })
            success_count += 1
        else:
            messages.append(f"[ERROR] {process_message}") # process_message already contains file and error
            error_files_details.append({"file": filename, "error": process_message})
            error_count += 1
            overall_success = False
            # If processing failed on the copy, the corrupted/original copy remains in output_dir.
            # Depending on desired behavior, could attempt to delete output_file_path here.

    final_summary_msg = f"Specific page removal finished. Total PDFs: {total_files_to_process}, Succeeded: {success_count}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files_to_process,
        "success_count": success_count,
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }


def repair_pdfs_by_rebuilding_api(input_dir: str, output_dir: str) -> dict:
    """
    API-adapted: Attempts to repair PDF internal structure by re-saving.
    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str): Directory to save repaired PDFs.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting PDF repair from '{input_dir}' to '{output_dir}'.")
    messages = []
    success_files_details = []  # List of {"original": "file.pdf", "repaired": "file.pdf"}
    error_files_details = []    # List of {"file": "file.pdf", "error": "error message"}
    processed_count = 0
    success_count = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for repair."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1}

    total_files_to_process = len(pdf_files)

    for filename in tqdm(pdf_files, desc="API Repairing PDFs", unit="file", disable=True):
        input_path = os.path.join(input_dir, filename)
        # Use a temporary file in the output directory to avoid issues if input_dir == output_dir
        temp_output_filename = f"~temp_repaired_{filename}"
        temp_output_path = os.path.join(output_dir, temp_output_filename)
        final_output_path = os.path.join(output_dir, filename)
        processed_count += 1

        try:
            with pikepdf.open(input_path, allow_overwriting_input=False) as pdf: # Open original
                pdf.save(temp_output_path) # Save to temp location in output_dir

            # If input_dir and output_dir are the same, and temp_output_path is different from final_output_path
            # (which it is due to ~temp_ prefix), then move.
            # If input_dir is different from output_dir, this move is also correct.
            if os.path.exists(final_output_path) and not os.path.samefile(temp_output_path, final_output_path):
                os.remove(final_output_path) # Remove existing target if overwriting
            shutil.move(temp_output_path, final_output_path)

            msg = f"Repair successful for '{filename}'. Saved to '{final_output_path}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({"original": filename, "repaired": filename})
            success_count += 1
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            msg = f"Repair failed for '{filename}': {type(e).__name__} - {error_msg}"
            module_logger.error(msg, exc_info=False)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": filename, "error": msg})
            error_count += 1
            overall_success = False
        finally:
            if os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except OSError as e_os:
                    module_logger.warning(f"Could not delete temporary file '{temp_output_path}': {e_os}")
    
    final_summary_msg = f"PDF repair process finished. Total PDFs: {total_files_to_process}, Succeeded: {success_count}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files_to_process,
        "success_count": success_count,
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }