# backend/modules/iso_creator.py
import os
import subprocess
import sys
import shutil
import re
import logging
import time
from tqdm import tqdm

module_logger = logging.getLogger(__name__)

def _create_iso_from_folder_hdiutil(source_folder: str, output_dir: str) -> tuple[bool, str, str]:
    """
    Internal helper: Uses hdiutil (macOS only) to create an ISO.
    Returns: (success_flag, message_or_path, iso_filename_or_error_detail)
    """
    if sys.platform != "darwin":
        return False, "ISO creation with hdiutil is supported only on macOS.", ""

    if shutil.which("hdiutil") is None:
        return False, "'hdiutil' command not found. Please ensure it's installed on your macOS system.", ""

    folder_name = os.path.basename(source_folder)
    # Replace characters that are problematic in filenames or paths for ISOs
    cleaned_name = re.sub(r'[\\/:*?"<>|()&;\']', '_', folder_name.strip())
    if not cleaned_name: # Handle case where folder_name consisted only of special chars
        cleaned_name = "iso_image"
    iso_filename = f"{cleaned_name}.iso"
    output_iso_path = os.path.join(output_dir, iso_filename)

    if os.path.exists(output_iso_path):
        return True, f"Skipping: Target ISO file already exists: {output_iso_path}", iso_filename

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        return False, f"Could not create output directory '{output_dir}': {e}", ""
    
    module_logger.info(f"Compressing with hdiutil: '{source_folder}' -> '{output_iso_path}'")
    cmd = ["hdiutil", "makehybrid", "-o", output_iso_path, source_folder, "-iso", "-joliet"]

    try:
        # Using a timeout for external processes is a good practice
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', timeout=300) # 5 min timeout
        module_logger.info(f"Successfully created ISO file: {output_iso_path}")
        return True, output_iso_path, iso_filename
    except subprocess.CalledProcessError as e:
        error_msg = f"hdiutil failed. Code: {e.returncode}. Stdout: {e.stdout.strip()}. Stderr: {e.stderr.strip()}"
        module_logger.error(error_msg)
        return False, error_msg, ""
    except subprocess.TimeoutExpired:
        error_msg = f"hdiutil command timed out for folder: {source_folder}"
        module_logger.error(error_msg)
        return False, error_msg, ""
    except FileNotFoundError: # Should be caught by shutil.which earlier, but as a safeguard
        error_msg = "'hdiutil' command not found."
        module_logger.error(error_msg)
        return False, error_msg, ""
    except Exception as e:
        error_msg = f"An unknown error occurred during ISO creation with hdiutil: {e}"
        module_logger.error(error_msg)
        return False, error_msg, ""

def process_subfolders_to_iso_api(parent_dirs_list: list, output_base_dir: str = None) -> dict:
    """
    API-adapted: Batch processes subfolders to create ISO files.
    Args:
        parent_dirs_list (list): List of parent directory paths.
        output_base_dir (str, optional): Base output directory. If None, ISOs are saved in parent_dirs.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting batch ISO creation for parent directories: {parent_dirs_list}")
    messages = []
    success_isos_details = []  # List of {"source_folder": "...", "iso_path": "...", "iso_name": "..."}
    skipped_isos_details = [] # List of {"source_folder": "...", "reason": "..."}
    error_isos_details = []    # List of {"source_folder": "...", "error": "..."}
    
    total_subfolders_found = 0
    success_count = 0
    skipped_count = 0
    error_count = 0
    overall_success = True # Becomes False if any critical error occurs

    # Platform check for the core ISO creation method
    if sys.platform != "darwin":
        msg = "ISO creation using the current method (hdiutil) is only supported on macOS."
        module_logger.error(msg)
        messages.append(f"[ERROR] {msg}")
        # Return an error structure indicating platform incompatibility for this specific function
        return {"success": False, "messages": messages, "platform_error": msg, 
                "total_subfolders_found":0, "success_count":0, "skipped_count":0, "error_count":1}

    if not isinstance(parent_dirs_list, list):
        msg = "Invalid 'parent_dirs_list'. It must be a list of directory paths."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    for parent_dir in parent_dirs_list:
        if not isinstance(parent_dir, str) or not os.path.isdir(parent_dir):
            msg = f"Skipping invalid parent directory: '{parent_dir}'"
            module_logger.warning(msg)
            messages.append(f"[WARN] {msg}")
            error_isos_details.append({"source_folder": parent_dir, "error": "Invalid or non-existent directory"})
            error_count +=1
            overall_success = False
            continue

        actual_output_dir = output_base_dir if output_base_dir else parent_dir
        module_logger.info(f"Processing subfolders in '{parent_dir}', outputting to '{actual_output_dir}'")
        
        try:
            subfolders = [f for f in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, f))]
        except Exception as e:
            msg = f"Could not list subfolders in '{parent_dir}': {e}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_isos_details.append({"source_folder": parent_dir, "error": f"Failed to list subfolders: {e}"})
            error_count += 1
            overall_success = False
            continue

        if not subfolders:
            msg = f"No subfolders found in '{parent_dir}'."
            module_logger.info(msg)
            messages.append(f"[INFO] {msg}")
            continue

        total_subfolders_found += len(subfolders)

        for subfolder_name in tqdm(subfolders, desc=f"Creating ISOs from {os.path.basename(parent_dir)}", unit="folder", disable=True):
            full_subfolder_path = os.path.join(parent_dir, subfolder_name)
            
            # Using the macOS specific hdiutil function
            iso_success, result_msg_or_path, iso_name = _create_iso_from_folder_hdiutil(full_subfolder_path, actual_output_dir)
            
            if iso_success:
                if "Skipping" in result_msg_or_path:
                    module_logger.info(result_msg_or_path)
                    messages.append(f"[SKIP] {result_msg_or_path}")
                    skipped_isos_details.append({"source_folder": subfolder_name, "reason": result_msg_or_path, "iso_name": iso_name})
                    skipped_count += 1
                else: # Actual success creating a new ISO
                    module_logger.info(f"Successfully created ISO: {iso_name} from {subfolder_name}")
                    messages.append(f"[SUCCESS] Created ISO: {iso_name} from {subfolder_name}")
                    success_isos_details.append({"source_folder": subfolder_name, "iso_path": result_msg_or_path, "iso_name": iso_name})
                    success_count += 1
            else: # Failure
                module_logger.error(f"Failed to create ISO for '{subfolder_name}': {result_msg_or_path}")
                messages.append(f"[ERROR] ISO creation failed for '{subfolder_name}': {result_msg_or_path}")
                error_isos_details.append({"source_folder": subfolder_name, "error": result_msg_or_path})
                error_count += 1
                overall_success = False
    
    final_summary_msg = (f"ISO creation process finished. Subfolders found: {total_subfolders_found}, "
                         f"Successfully created: {success_count}, Skipped: {skipped_count}, Failed: {error_count}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_subfolders_found": total_subfolders_found,
        "success_count": success_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "successful_isos": success_isos_details,
        "skipped_isos": skipped_isos_details,
        "failed_isos": error_isos_details
    }