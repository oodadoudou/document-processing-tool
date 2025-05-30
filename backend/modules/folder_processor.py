# backend/modules/folder_processor.py
import os
import shutil
import logging
import time
from tqdm import tqdm
from pathlib import Path
import zipfile
import py7zr


module_logger = logging.getLogger(__name__)

def encode_folders_with_double_compression_api(input_dir: str, password: str = "1111") -> dict:
    """
    API-adapted: Encodes and double-compresses items using Python libraries (py7zr, zipfile).
    Args:
        input_dir (str): Directory containing files/folders to process.
        password (str): Password for 7z encryption.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting double compression (Python libs) in '{input_dir}' with provided password.")
    messages = []
    successful_items_details = []  # List of {"original_item": "...", "final_archive": "..."}
    failed_items_details = []      # List of {"item": "...", "error": "..."}
    processed_item_count = 0
    success_count = 0
    error_count = 0
    overall_success = True

    if not password: # Password is required for 7z
        msg = "Password cannot be empty for 7z encryption."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}
    
    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        items_to_process_names = [
            f for f in os.listdir(input_dir)
            if f not in ["processed_files", "decoded_files"] and not f.startswith('.')
            and not f.endswith(".z删ip") # Avoid re-processing already processed files
        ]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not items_to_process_names:
        msg = "No eligible items found for encoding in the input directory."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_item_count": 0, "success_count": 0, "error_count": 0}

    total_items_to_process = len(items_to_process_names)

    for item_name in tqdm(items_to_process_names, desc="API Encoding Items (Python Libs)", unit="item", disable=True):
        full_item_path = os.path.join(input_dir, item_name)
        item_base_name = Path(item_name).stem if os.path.isfile(full_item_path) else item_name
        
        # Define intermediate and final file paths relative to input_dir
        sevenz_temp_filename = f"{item_base_name}.7z"
        renamed_sevenz_filename = f"{item_base_name}.7删z" # Contains '删'
        zip_temp_filename = f"{item_base_name}.zip"
        final_output_filename = f"{item_base_name}.z删ip" # Contains '删'

        sevenz_temp_path = os.path.join(input_dir, sevenz_temp_filename)
        renamed_sevenz_path = os.path.join(input_dir, renamed_sevenz_filename)
        zip_temp_path = os.path.join(input_dir, zip_temp_filename)
        final_output_path = os.path.join(input_dir, final_output_filename)
        
        processed_item_count += 1
        current_item_success = True

        try:
            # Step 1: Compress to .7z with password using py7zr
            module_logger.info(f"Encoding '{item_name}': Step 1/4 - Compressing to '{sevenz_temp_filename}' with py7zr...")
            with py7zr.SevenZipFile(sevenz_temp_path, 'w', password=password) as archive:
                if os.path.isdir(full_item_path):
                    archive.writeall(full_item_path, arcname=item_name) # arcname stores the folder with its name
                else: # is a file
                    # Create a temporary folder with the same name as the file (without extension)
                    temp_folder_name = item_base_name
                    temp_folder_path = os.path.join(input_dir, temp_folder_name)
                    try:
                        os.makedirs(temp_folder_path, exist_ok=True)
                        # Move the file into the temporary folder
                        shutil.move(full_item_path, os.path.join(temp_folder_path, item_name))
                        # Compress the temporary folder
                        archive.writeall(temp_folder_path, arcname=temp_folder_name)
                        # Move the file back to its original location
                        shutil.move(os.path.join(temp_folder_path, item_name), full_item_path)
                        # Remove the temporary folder
                        os.rmdir(temp_folder_path)
                    except Exception as e:
                        # Clean up in case of error
                        if os.path.exists(temp_folder_path):
                            if os.path.exists(os.path.join(temp_folder_path, item_name)):
                                shutil.move(os.path.join(temp_folder_path, item_name), full_item_path)
                            os.rmdir(temp_folder_path)
                        raise e
            messages.append(f"[INFO] '{item_name}' compressed to '{sevenz_temp_filename}'.")

            # Step 2: Rename .7z to .7删z
            module_logger.info(f"Encoding '{item_name}': Step 2/4 - Renaming to '{renamed_sevenz_filename}'...")
            os.rename(sevenz_temp_path, renamed_sevenz_path)
            messages.append(f"[INFO] Renamed to '{renamed_sevenz_filename}'.")

            # Step 3: Compress .7删z to .zip (no encryption) using zipfile
            module_logger.info(f"Encoding '{item_name}': Step 3/4 - Compressing to '{zip_temp_filename}' with zipfile...")
            with zipfile.ZipFile(zip_temp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(renamed_sevenz_path, arcname=os.path.basename(renamed_sevenz_filename))
            messages.append(f"[INFO] Compressed to '{zip_temp_filename}'.")

            # Clean up intermediate .7删z file
            os.remove(renamed_sevenz_path)
            messages.append(f"[INFO] Cleaned up '{renamed_sevenz_filename}'.")

            # Step 4: Rename .zip to .z删ip
            module_logger.info(f"Encoding '{item_name}': Step 4/4 - Renaming to '{final_output_filename}'...")
            os.rename(zip_temp_path, final_output_path)
            messages.append(f"[SUCCESS] Item '{item_name}' successfully encoded to '{final_output_filename}'.")
            successful_items_details.append({"original_item": item_name, "final_archive": final_output_filename})
            success_count += 1

        except Exception as e:
            error_msg_detail = f"Encoding failed for '{item_name}': {type(e).__name__} - {str(e).splitlines()[0]}"
            module_logger.error(error_msg_detail, exc_info=False)
            messages.append(f"[ERROR] {error_msg_detail}")
            failed_items_details.append({"item": item_name, "error": error_msg_detail})
            error_count += 1
            overall_success = False
            current_item_success = False
        finally:
            # Cleanup any temp files if they still exist from this item's processing
            for temp_file in [sevenz_temp_path, renamed_sevenz_path, zip_temp_path]:
                if os.path.exists(temp_file):
                    try: os.remove(temp_file)
                    except Exception as e_clean: 
                        messages.append(f"[WARN] Failed to clean temp file '{os.path.basename(temp_file)}': {e_clean}")
            if not current_item_success and os.path.exists(final_output_path): # If failed, remove potentially incomplete final output
                 try: os.remove(final_output_path)
                 except Exception as e_clean_final:
                     messages.append(f"[WARN] Failed to clean potentially incomplete final output '{os.path.basename(final_output_path)}': {e_clean_final}")


    final_summary_msg = (f"Folder encoding process finished. Items processed: {processed_item_count}, "
                         f"Succeeded: {success_count}, Failed: {error_count}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")
    
    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_items_processed": total_items_to_process, # Total items found eligible
        "successful_encodings": success_count,
        "failed_encodings": error_count,
        "success_details": successful_items_details,
        "error_details": failed_items_details
    }


def decode_folders_with_double_decompression_api(input_dir: str, password: str = "1111") -> dict:
    """
    API-adapted: Decodes and double-decompresses .z删ip files using Python libraries.
    Decoded contents are extracted into the input_dir.
    Args:
        input_dir (str): Directory containing .z删ip files and where output will be placed.
        password (str): Password for 7z decryption.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting double decompression (Python libs) in '{input_dir}' with provided password.")
    messages = []
    successful_files_details = []  # List of {"encoded_file": "...", "extracted_content_name": "..."}
    failed_files_details = []      # List of {"encoded_file": "...", "error": "..."}
    processed_archive_count = 0
    success_count = 0
    error_count = 0
    overall_success = True

    if not password:
        msg = "Password cannot be empty for 7z decryption."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        encoded_files = [f for f in os.listdir(input_dir) if f.endswith(".z删ip")]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not encoded_files:
        msg = "No encoded files (.z删ip) found for decoding in the input directory."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_archive_count": 0, "success_count": 0, "error_count": 0}

    total_archives_to_process = len(encoded_files)

    for encoded_filename in tqdm(encoded_files, desc="API Decoding Files (Python Libs)", unit="file", disable=True):
        full_zsanip_path = os.path.join(input_dir, encoded_filename)
        item_base_name = Path(encoded_filename).stem # e.g., "my_folder" from "my_folder.z删ip"
        
        temp_zip_filename = f"{item_base_name}.zip"
        expected_7sanz_in_zip = f"{item_base_name}.7删z" # Name of the file inside the zip
        
        temp_zip_path = os.path.join(input_dir, temp_zip_filename)
        extracted_7sanz_path = os.path.join(input_dir, expected_7sanz_in_zip) # Where .7删z is extracted
        final_7z_path = os.path.join(input_dir, f"{item_base_name}.7z") # Renamed from .7删z

        processed_archive_count += 1
        current_archive_success = True
        extracted_content_final_name = None

        try:
            # Step 1: Copy .z删ip and rename the copy to .zip
            module_logger.info(f"Decoding '{encoded_filename}': Step 1/4 - Copying and renaming to '{temp_zip_filename}'...")
            shutil.copy2(full_zsanip_path, temp_zip_path)
            messages.append(f"[INFO] Copied '{encoded_filename}' to '{temp_zip_filename}'.")

            # Step 2: Decompress .zip to get .7删z using zipfile
            module_logger.info(f"Decoding '{encoded_filename}': Step 2/4 - Decompressing '{temp_zip_filename}'...")
            with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                if expected_7sanz_in_zip not in zf.namelist():
                    raise FileNotFoundError(f"'{expected_7sanz_in_zip}' not found inside '{temp_zip_filename}'. Available: {zf.namelist()}")
                zf.extract(expected_7sanz_in_zip, path=input_dir) # Extracts to input_dir/expected_7sanz_in_zip
            messages.append(f"[INFO] Extracted '{expected_7sanz_in_zip}' from zip.")
            
            if not os.path.exists(extracted_7sanz_path):
                raise FileNotFoundError(f"Intermediate file '{expected_7sanz_in_zip}' not found after ZIP extraction.")

            # Step 3: Rename .7删z to .7z
            module_logger.info(f"Decoding '{encoded_filename}': Step 3/4 - Renaming '{expected_7sanz_in_zip}' to '{os.path.basename(final_7z_path)}'...")
            os.rename(extracted_7sanz_path, final_7z_path)
            messages.append(f"[INFO] Renamed to '{os.path.basename(final_7z_path)}'.")

            # Step 4: Decompress .7z with password using py7zr, extracting into input_dir
            module_logger.info(f"Decoding '{encoded_filename}': Step 4/4 - Decompressing '{os.path.basename(final_7z_path)}' to '{input_dir}'...")
            with py7zr.SevenZipFile(final_7z_path, 'r', password=password) as archive:
                archive_names = archive.getnames()
                if archive_names: # Get the name of the first item, assuming it's the root folder/file
                    extracted_content_final_name = archive_names[0].split(os.sep)[0] # Get top-level item name
                archive.extractall(path=input_dir)
            messages.append(f"[SUCCESS] Decompressed '{os.path.basename(final_7z_path)}'. Extracted content: '{extracted_content_final_name or 'content'}'")
            successful_files_details.append({"encoded_file": encoded_filename, "extracted_content_name": extracted_content_final_name or "Unknown"})
            success_count +=1

        except py7zr.exceptions.PasswordRequired:
            error_msg_detail = f"Decoding failed for '{encoded_filename}': Password required or incorrect for 7z archive."
            module_logger.error(error_msg_detail)
            messages.append(f"[ERROR] {error_msg_detail}")
            failed_files_details.append({"encoded_file": encoded_filename, "error": "Incorrect 7z password or password required."})
            error_count += 1
            overall_success = False
            current_archive_success = False
        except Exception as e:
            error_msg_detail = f"Decoding failed for '{encoded_filename}': {type(e).__name__} - {str(e).splitlines()[0]}"
            module_logger.error(error_msg_detail, exc_info=False)
            messages.append(f"[ERROR] {error_msg_detail}")
            failed_files_details.append({"encoded_file": encoded_filename, "error": error_msg_detail})
            error_count += 1
            overall_success = False
            current_archive_success = False
        finally:
            # Clean up intermediate files
            for temp_file in [temp_zip_path, extracted_7sanz_path, final_7z_path]:
                if os.path.exists(temp_file):
                    try: os.remove(temp_file)
                    except Exception as e_clean:
                        messages.append(f"[WARN] Failed to clean temp file '{os.path.basename(temp_file)}': {e_clean}")
            
            # Cleanup partially extracted content if this archive failed
            if not current_archive_success and extracted_content_final_name:
                path_to_cleanup = os.path.join(input_dir, extracted_content_final_name)
                if os.path.exists(path_to_cleanup) and not path_to_cleanup.endswith(".z删ip"): # Basic safety
                    module_logger.warning(f"Attempting to cleanup partially extracted content: '{path_to_cleanup}'")
                    try:
                        if os.path.isdir(path_to_cleanup): shutil.rmtree(path_to_cleanup)
                        else: os.remove(path_to_cleanup)
                        messages.append(f"[INFO] Cleaned up partially extracted '{extracted_content_final_name}'.")
                    except Exception as e_clean_extracted:
                         messages.append(f"[WARN] Failed to cleanup partially extracted '{extracted_content_final_name}': {e_clean_extracted}")


    final_summary_msg = (f"Folder decoding process finished. Archives processed: {processed_archive_count}, "
                         f"Succeeded: {success_count}, Failed: {error_count}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_archives_processed": total_archives_to_process,
        "successful_decodings": success_count,
        "failed_decodings": error_count,
        "success_details": successful_files_details,
        "error_details": failed_files_details
    }