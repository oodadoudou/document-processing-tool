# backend/modules/file_combiner.py
import os
import re
import logging
import time
from tqdm import tqdm
import pikepdf # For PDF combining

module_logger = logging.getLogger(__name__)

def natural_sort_key(s: str) -> list:
    """
    Generates a natural sort key for intelligent sorting of filenames.
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]

def _combine_pdfs_for_api(input_dir: str, files_to_combine: list, output_path: str) -> tuple[list, list]:
    """
    Internal helper: Core logic for merging PDF files using pikepdf.
    Returns:
        tuple: (list_of_successfully_merged_filenames, list_of_failed_file_details)
    """
    succeeded_filenames = []
    failed_file_details = [] # List of (filename, error_message)
    
    # Create a new PDF object to which pages from other PDFs will be appended
    new_pdf = pikepdf.Pdf.new() 
    
    for filename in tqdm(files_to_combine, desc="API Merging PDFs", unit="file", disable=True):
        file_path = os.path.join(input_dir, filename)
        try:
            with pikepdf.open(file_path) as src_pdf:
                new_pdf.pages.extend(src_pdf.pages)
            succeeded_filenames.append(filename)
            module_logger.info(f"Successfully appended '{filename}' to merge list.")
        except Exception as e:
            error_detail = str(e).split('\n')[0]
            failed_file_details.append((filename, error_detail))
            module_logger.error(f"Failed to process PDF '{filename}' for merging: {error_detail}")
            
    if not succeeded_filenames and failed_file_details: # All files failed to be processed
        # Do not save if no files were successfully processed and there were errors.
        # If succeeded_filenames is empty but failed_file_details is also empty, it means no files were processed (e.g. input list was empty)
        # which should be handled by the caller.
        module_logger.error("No PDF files were successfully processed for merging. Output PDF not saved.")
        # new_pdf.close() # Not strictly necessary as it wasn't saved
        return succeeded_filenames, failed_file_details

    if not new_pdf.pages: # If no pages were added (e.g., all source PDFs were empty or unreadable)
        module_logger.warning("No pages were added to the new PDF. Saving an empty PDF or skipping.")
        # Decide on behavior: save empty PDF or raise error/return specific status
        # For now, let's save it if at least one file was "successfully" opened even if it had no pages.
        # If succeeded_filenames is empty, this block won't be reached if there were errors.
        if not succeeded_filenames: # No files were even attempted or all failed before page extend
             return succeeded_filenames, failed_file_details


    try:
        new_pdf.save(output_path)
        module_logger.info(f"Successfully saved merged PDF to '{output_path}'")
    except Exception as e_save:
        error_detail = f"Failed to save merged PDF '{output_path}': {str(e_save).splitlines()[0]}"
        module_logger.error(error_detail)
        # Add a general error for the saving process if it fails
        # This is tricky because individual files might have been "successful" in appending
        # We might need a way to signify that the final save failed.
        # For now, if save fails, consider the whole operation a failure for the output file.
        # We'll rely on the overall success flag in the main API function.
        # Add a specific failure for the output file itself.
        failed_file_details.append((os.path.basename(output_path), error_detail))
    finally:
        # pikepdf objects are context managed by 'with', but if new_pdf was created outside,
        # it doesn't have a close method like file objects. It's managed by Python's GC.
        pass
        
    return succeeded_filenames, failed_file_details


def _combine_txts_for_api(input_dir: str, files_to_combine: list, output_path: str) -> tuple[list, list]:
    """
    Internal helper: Core logic for merging TXT files.
    Returns:
        tuple: (list_of_successfully_merged_filenames, list_of_failed_file_details)
    """
    succeeded_filenames = []
    failed_file_details = [] # List of (filename, error_message)

    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for filename in tqdm(files_to_combine, desc="API Merging TXTs", unit="file", disable=True):
                file_path = os.path.join(input_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                        content = infile.read()
                        outfile.write(content)
                        outfile.write('\n') # Add a newline between concatenated files
                    succeeded_filenames.append(filename)
                    module_logger.info(f"Successfully appended '{filename}' to '{os.path.basename(output_path)}'.")
                except Exception as e:
                    error_detail = str(e).split('\n')[0]
                    failed_file_details.append((filename, error_detail))
                    module_logger.error(f"Failed to read/write TXT file '{filename}': {error_detail}")
        module_logger.info(f"Successfully saved merged TXT to '{output_path}'")
    except Exception as e_save: # Error opening the output file
        error_detail = f"Failed to open or write to output file '{output_path}': {str(e_save).splitlines()[0]}"
        module_logger.error(error_detail)
        failed_file_details.append((os.path.basename(output_path), error_detail)) # General failure for output
        # If output file couldn't be opened, all individual "successes" are moot.
        succeeded_filenames = [] # Reset successes as the main operation failed

    return succeeded_filenames, failed_file_details


def combine_files_api(input_dir: str, output_dir: str, file_type_char: str, output_base_name: str) -> dict:
    """
    API-adapted: Combines multiple files of the same type into a single file.
    Args:
        input_dir (str): Directory containing files to merge.
        output_dir (str): Directory to save the merged file.
        file_type_char (str): 'p' for PDF, 't' for TXT.
        output_base_name (str): Base name for the output merged file (without extension).
    Returns:
        dict: Operation results including success status and processed files details.
    """
    module_logger.info(f"API: Combining '{file_type_char}' files from '{input_dir}' to '{output_dir}/{output_base_name}'.")
    messages = []
    successful_input_files = []
    failed_input_file_details = []  # List of {"file": "...", "error": "..."}
    overall_success = True
    final_output_path = None

    # Map file type characters to extensions
    ext_map = {'p': '.pdf', 't': '.txt'}
    if file_type_char not in ext_map:
        msg = f"Invalid file_type_char: '{file_type_char}'. Supported: {', '.join(ext_map.keys())}."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    target_extension = ext_map[file_type_char]
    
    # Input validation
    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    # Get list of files to combine, sorted naturally
    try:
        files_to_combine = sorted(
            [f for f in os.listdir(input_dir) if f.lower().endswith(target_extension)],
            key=natural_sort_key
        )
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not files_to_combine:
        msg = f"No '{target_extension}' files found in '{input_dir}' for merging."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "total_input_files_found": 0, "files_merged_count": 0, "file_processing_errors": 0}

    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    # Prepare output path
    output_filename_with_ext = f"{output_base_name}{target_extension}" if not output_base_name.lower().endswith(target_extension) else output_base_name
    final_output_path = os.path.join(output_dir, output_filename_with_ext)

    messages.append(f"[INFO] Attempting to merge {len(files_to_combine)} '{target_extension}' files into '{final_output_path}'.")
    messages.append("[INFO] Files to be processed in order:")
    for i, f_name in enumerate(files_to_combine, 1):
        messages.append(f"[INFO] {i:02d}. {f_name}")

    # Process files based on type
    if file_type_char == 'p':
        successful_input_files, failed_details_list = _combine_pdfs_for_api(input_dir, files_to_combine, final_output_path)
    elif file_type_char == 't':
        successful_input_files, failed_details_list = _combine_txts_for_api(input_dir, files_to_combine, final_output_path)
    else:
        msg = f"Internal error: No handler for file type '{file_type_char}'."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    # Process results
    for fname, err in failed_details_list:
        failed_input_file_details.append({"file": fname, "error": err})
        messages.append(f"[ERROR] Processing '{fname}': {err}")
    
    error_count = len(failed_input_file_details)
    if error_count > 0 or not os.path.exists(final_output_path): # If any individual file failed OR final output wasn't saved
        overall_success = False
        if os.path.exists(final_output_path) and error_count > 0 : # Output exists but some inputs failed
             messages.append(f"[WARN] Merged file '{output_filename_with_ext}' was created but some input files failed to process.")
        elif not os.path.exists(final_output_path):
             messages.append(f"[ERROR] Final merged file '{output_filename_with_ext}' was NOT created.")


    if overall_success and os.path.exists(final_output_path):
        final_summary_msg = f"File combination successful. Merged {len(successful_input_files)} files into '{output_filename_with_ext}'."
        messages.append(f"[SUCCESS] {final_summary_msg}")
    else:
        final_summary_msg = f"File combination process finished with issues. Successfully processed inputs: {len(successful_input_files)}, Failures: {error_count}."
        messages.append(f"[INFO] {final_summary_msg}")


    module_logger.info(final_summary_msg)
    
    return {
        "success": overall_success,
        "messages": messages,
        "total_input_files_found": len(files_to_combine),
        "files_successfully_processed": len(successful_input_files),
        "file_processing_errors": error_count,
        "output_file_path": final_output_path if overall_success and os.path.exists(final_output_path) else None,
        "output_filename": output_filename_with_ext if overall_success and os.path.exists(final_output_path) else None,
        "error_details": failed_input_file_details
    }