import os
import subprocess
import sys
import shutil
import re
import logging
import time
from tqdm import tqdm

try:
    from modules import report_generator
except ImportError:
    import report_generator

logger = logging.getLogger(__name__)


def create_iso_from_folder(source_folder: str, output_dir: str) -> tuple[bool, str]:
    """
    Uses hdiutil makehybrid to compress the specified folder into an ISO,
    preserving Chinese encoding and avoiding mkisofs garbled characters and mounting issues.

    Args:
        source_folder (str): The path to the source folder to be compressed.
        output_dir (str): The target directory where the ISO file will be saved.

    Returns:
        tuple[bool, str]: (True, output_iso_path) if successful, (False, error_message) otherwise.
    """
    if sys.platform != "darwin":
        return False, "This feature is currently supported only on macOS systems."

    if shutil.which("hdiutil") is None:
        return False, "'hdiutil' command not found. Please ensure your macOS system is complete."

    folder_name = os.path.basename(source_folder)
    cleaned_name = re.sub(r'[\\/:*?"<>|]', '_', folder_name.strip())
    output_iso_path = os.path.join(output_dir, f"{cleaned_name}.iso")

    if os.path.exists(output_iso_path):
        return True, f"Skipping: Target ISO file already exists: {output_iso_path}"

    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Compressing: {source_folder} --> {output_iso_path}")

    cmd = [
        "hdiutil", "makehybrid",
        "-o", output_iso_path,
        source_folder,
        "-iso", "-joliet"
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        logger.info(f"Successfully created ISO file: {output_iso_path}")
        return True, output_iso_path
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to create ISO. Error code: {e.returncode}\nStdout: {e.stdout.strip()}\nStderr: {e.stderr.strip()}"
        logger.error(error_msg)
        return False, error_msg
    except FileNotFoundError:
        error_msg = "'hdiutil' command not found. Please ensure it's installed and in your system PATH."
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unknown error occurred during ISO creation: {e}"
        logger.error(error_msg)
        return False, error_msg

def process_subfolders_to_iso(parent_dirs_list: list, output_base_dir: str = None):
    """
    Batch processes all subfolders within specified parent directories,
    compressing each subfolder into an individual ISO file.

    Args:
        parent_dirs_list (list): A list of parent directory paths to process.
        output_base_dir (str, optional): The base output directory where ISO files will be saved.
                                         If None, ISO files will be saved in their respective parent directories.
    """
    logger.info("Starting batch compression of subfolders to ISO")

    total_folders_processed = 0
    successful_isos = []
    failed_isos = []
    start_time = time.time()

    for parent_dir in parent_dirs_list:
        actual_output_dir = output_base_dir if output_base_dir else parent_dir

        logger.info(f"Processing directory: {parent_dir}")
        if not os.path.isdir(parent_dir):
            logger.warning(f"Skipping: '{parent_dir}' is not a valid directory or does not exist.")
            failed_isos.append((parent_dir, "Invalid directory"))
            continue

        subfolders = [f for f in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, f))]
        if not subfolders:
            logger.warning(f"No subfolders found in '{parent_dir}' to process.")
            continue

        for subfolder in tqdm(subfolders, desc=f"Creating ISOs in {parent_dir}"):
            total_folders_processed += 1
            full_subfolder_path = os.path.join(parent_dir, subfolder)
            
            success, result_message = create_iso_from_folder(full_subfolder_path, actual_output_dir)
            
            if success:
                # If create_iso_from_folder returns True and a path, it's a success
                # It might also return True and a "Skipping" message for existing files.
                # We need to differentiate actual new ISO creation from skipping.
                if "Skipping" in result_message:
                    logger.info(result_message) # Log the skip message
                else:
                    successful_isos.append(os.path.basename(result_message)) # result_message is the path
            else:
                failed_isos.append((subfolder, result_message))

    duration = time.time() - start_time
    logger.info("All folders have been processed.")
    
    report_generator.generate_report(
        report_title="ISO Creation Report",
        total_processed=total_folders_processed,
        success_files=successful_isos,
        error_files=failed_isos,
        duration=duration
    )