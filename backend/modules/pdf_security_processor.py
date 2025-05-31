# backend/modules/pdf_security_processor.py
import os
import time
import logging
import pikepdf
from tqdm import tqdm

module_logger = logging.getLogger(__name__)

def encode_pdfs_api(input_dir: str, output_dir: str, password: str) -> dict:
    """
    API-adapted: PDF Encryption Function (AES-256 Encryption).
    Args:
        input_dir (str): The directory containing PDF files to encrypt.
        output_dir (str): Directory to save encrypted PDFs.
        password (str): Encryption password.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting PDF encryption from '{input_dir}' to '{output_dir}' with provided password.")
    messages = []
    success_files_details = []  # List of {"original": "file.pdf", "encrypted": "encrypted_file.pdf"}
    error_files_details = []    # List of {"file": "file.pdf", "error": "error message"}
    processed_count = 0 # Counts files attempted
    success_count = 0
    error_count = 0
    overall_success = True

    if not password:
        msg = "Password cannot be empty for encryption."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for encryption."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0, "success_files": [], "error_files": []}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    total_files = len(pdf_files)

    for filename in tqdm(pdf_files, desc="API Encrypting PDFs", unit="file", disable=True):
        input_path = os.path.join(input_dir, filename)
        output_filename = f"encrypted_{filename}"
        output_path = os.path.join(output_dir, output_filename)
        processed_count +=1

        try:
            with pikepdf.open(input_path) as pdf:
                if pdf.is_encrypted:
                    msg = f"Skipping '{filename}': PDF is already encrypted."
                    module_logger.warning(msg)
                    messages.append(f"[WARN] {msg}")
                    error_files_details.append({"file": filename, "error": "Already encrypted"})
                    error_count +=1 
                    continue

                permissions_to_set = pikepdf.Permissions() # Start with default (all True)
                try:
                    # Attempt to set desired restrictions
                    permissions_to_set.copy_content = False
                    permissions_to_set.extract_content_accessibility = False
                    permissions_to_set.modify_content = False
                    permissions_to_set.modify_annotations = False 
                    permissions_to_set.fill_forms = False 
                    permissions_to_set.assemble_document = False
                    permissions_to_set.print_low_resolution = False
                    permissions_to_set.print_high_resolution = False
                except AttributeError as e_attr:
                    # Log a warning if specific permissions cannot be set
                    warning_msg = (f"Could not set specific PDF permissions for '{filename}' due to an AttributeError "
                                   f"('{e_attr}'). The PDF will be encrypted with default permissions, which might be "
                                   "less restrictive than intended. Please check your pikepdf library version "
                                   "and installation (version 3.0+ recommended).")
                    module_logger.warning(warning_msg)
                    messages.append(f"[WARN] {warning_msg}")
                    # 'permissions_to_set' remains the default pikepdf.Permissions() object (all flags True)
                    # This means we are "allowing" all these actions from pikepdf's perspective.
                    # However, PDF viewers often apply their own restrictive defaults when a user password is set.

                pdf.save(output_path, encryption=pikepdf.Encryption(
                    user=password,
                    owner=password, 
                    allow=permissions_to_set # Pass the (potentially modified or default) permissions object
                ))
            success_count += 1
            msg = f"Encryption successful: '{filename}' -> '{output_filename}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({"original": filename, "encrypted": output_filename})
        except pikepdf.PasswordError: 
            msg = f"Skipping '{filename}': PDF is likely already encrypted and password protected."
            module_logger.warning(msg)
            messages.append(f"[WARN] {msg}")
            error_files_details.append({"file": filename, "error": "Already encrypted or password error on open"})
            error_count +=1
        except Exception as e:
            # Catch other general exceptions during the encryption process
            error_msg = str(e).split('\n')[0]
            full_error_msg = f"Encryption failed for '{filename}': {type(e).__name__} - {error_msg}"
            module_logger.error(full_error_msg, exc_info=True) 
            messages.append(f"[ERROR] {full_error_msg}")
            error_files_details.append({"file": filename, "error": full_error_msg}) # Store the full error message
            error_count += 1
            overall_success = False
    
    final_summary_msg = f"PDF encryption finished. Total PDFs: {total_files}, Succeeded: {success_count}, Failed/Skipped: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0, 
        "messages": messages,
        "total_processed": total_files, 
        "success_count": success_count,
        "error_count": error_count, 
        "success_files": success_files_details,
        "error_files": error_files_details
    }

def decode_pdfs_api(input_dir: str, password: str) -> dict:
    """
    API-adapted: Decrypts password-protected PDF files.
    Args:
        input_dir (str): The directory containing PDF files to decrypt.
        password (str): Decryption password.
    Returns:
        dict: Operation results including success status and processed files details.
    """
    module_logger.info(f"API: Starting PDF decryption in '{input_dir}' with provided password.")
    messages = []
    success_files_details = []  # List of {"file": "filename.pdf", "status": "decrypted"}
    error_files_details = []    # List of {"file": "filename.pdf", "error": "error message"}
    processed_count = 0
    success_count = 0
    error_count = 0
    overall_success = True

    # Input validation
    if not password:
        msg = "Password cannot be empty for decryption."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "success_count": 0, "error_count": 1, "success_files": [], "error_files": []}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for decryption."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0, "success_files": [], "error_files": []}

    total_files = len(pdf_files)

    for filename in tqdm(pdf_files, desc="API Decrypting PDFs", unit="file", disable=True):
        input_path = os.path.join(input_dir, filename)
        temp_filename = f"~decr_temp_{filename}"
        temp_path = os.path.join(input_dir, temp_filename)
        processed_count +=1

        try:
            with pikepdf.open(input_path, password=password, allow_overwriting_input=True) as pdf:
                if not pdf.is_encrypted:
                    msg = f"Skipping '{filename}': PDF is not encrypted."
                    module_logger.info(msg)
                    messages.append(f"[INFO] {msg}")
                    continue 
                
                pdf.save(temp_path) 
            
            os.replace(temp_path, input_path)
            success_count += 1
            msg = f"Decryption successful: '{filename}' (overwritten)"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            success_files_details.append({"file": filename, "status": "decrypted"})

        except pikepdf.PasswordError:
            error_msg = "Incorrect password or PDF is not encrypted with this password."
            msg = f"Decryption failed for '{filename}': {error_msg}"
            module_logger.warning(msg) 
            messages.append(f"[FAIL] {msg}") 
            error_files_details.append({"file": filename, "error": error_msg})
            error_count += 1
            overall_success = False 
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            msg = f"Error processing '{filename}' for decryption: {type(e).__name__} - {error_msg}"
            module_logger.error(msg, exc_info=False)
            messages.append(f"[ERROR] {msg}")
            error_files_details.append({"file": filename, "error": msg})
            error_count += 1
            overall_success = False
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as e_os:
                    module_logger.warning(f"Could not delete temporary file '{temp_path}': {e_os}")
    
    final_summary_msg = f"PDF decryption finished. Total PDFs: {total_files}, Succeeded: {success_count}, Failed: {error_count}."
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_processed": total_files,
        "success_count": success_count,
        "error_count": error_count,
        "success_files": success_files_details,
        "error_files": error_files_details
    }
