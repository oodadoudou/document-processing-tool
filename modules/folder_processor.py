import os
import subprocess
import shutil
import logging
import time
from tqdm import tqdm
from pathlib import Path
import platform
try:
    from modules import report_generator
except ImportError:
    import report_generator

logger = logging.getLogger(__name__)

def _check_command_exists(command: str) -> bool:
    """Checks if a given command exists in the system's PATH."""
    return shutil.which(command) is not None

def _log_missing_command_error(command: str) -> None:
    """Logs a platform-specific error message for a missing command."""
    system = platform.system()
    error_message = f"Error: '{command}' command not found."

    if command == "7z":
        if system == "Windows":
            error_message += " Please install 7-Zip from https://www.7-zip.org/ and ensure its executable directory (e.g., C:\\Program Files\\7-Zip) is added to your system's PATH environment variable."
        elif system == "Darwin": # macOS
            error_message += " Please install p7zip via Homebrew: 'brew install p7zip'"
        elif system == "Linux":
            error_message += " Please install p7zip-full: 'sudo apt-get install p7zip-full' (Debian/Ubuntu) or 'sudo yum install p7zip-full' (RedHat/CentOS)."
        else:
            error_message += " Please install '7z' according to your operating system's package manager or official website."
    elif command in ["zip", "unzip"]:
        if system == "Windows":
            error_message += " These commands are usually available via Git Bash, Windows Subsystem for Linux (WSL), or can be installed with Chocolatey: 'choco install zip' / 'choco install unzip'."
        elif system == "Darwin": # macOS
            error_message += " These commands are usually pre-installed on macOS. If not, try reinstalling macOS command-line tools or Homebrew's 'zip' package."
        elif system == "Linux":
            error_message += " Please install them: 'sudo apt-get install zip unzip' (Debian/Ubuntu) or 'sudo yum install zip unzip' (RedHat/CentOS)."
        else:
            error_message += f" Please install '{command}' according to your operating system's package manager or official website."
    
    logger.error(error_message)


def encode_folders_with_double_compression(input_dir: str, password: str = "1111") -> None:
    """
    Encodes and double-compresses all first-level files and directories in the input_dir.
    Processes each item:
    1. Compresses to .7z with a password.
    2. Renames .7z to .7删z.
    3. Compresses .7删z to .zip (no encryption).
    4. Renames .zip to .z删ip.
    5. Cleans up intermediate files.

    Args:
        input_dir (str): The directory containing the files/folders to be processed.
        password (str): The password for the initial 7z encryption (default: "1111").
    """
    logger.info(f"Starting double compression and encoding of items in: {input_dir}")

    # Check for required external commands with OS-specific messages
    if not _check_command_exists("7z"):
        _log_missing_command_error("7z")
        return
    if not _check_command_exists("zip"):
        _log_missing_command_error("zip")
        return

    # Get all first-level items (files and directories)
    # Exclude special directories and hidden files
    items_to_process = [
        f for f in os.listdir(input_dir)
        if f != "processed_files" and f != "decoded_files" and not f.startswith('.')
    ]
    
    if not items_to_process:
        logger.warning(f"No files or folders found in '{input_dir}' for processing (excluding hidden files and tool directories).")
        return

    successful_items = []
    failed_items = []
    start_time = time.time()

    for item_name in tqdm(items_to_process, desc="Encoding Items"):
        full_item_path = os.path.join(input_dir, item_name)
        
        # Determine base name for intermediate archives and final output
        # For both files and directories, the base name for the .z删ip will be the item's name without its original extension (if it's a file).
        # This ensures "my_document.pdf" -> "my_document.z删ip" and "my_folder" -> "my_folder.z删ip".
        item_base_name_for_archive = Path(item_name).stem if os.path.isfile(full_item_path) else item_name
        
        # Define intermediate and final file paths, all in input_dir
        sevenz_temp_name = f"{item_base_name_for_archive}.7z"
        renamed_sevenz_name = f"{item_base_name_for_archive}.7删z"
        zip_temp_name = f"{item_base_name_for_archive}.zip" # Use .zip temporarily
        final_output_name = f"{item_base_name_for_archive}.z删ip"

        sevenz_temp_path = os.path.join(input_dir, sevenz_temp_name)
        renamed_sevenz_path = os.path.join(input_dir, renamed_sevenz_name)
        zip_temp_path = os.path.join(input_dir, zip_temp_name)
        final_output_path = os.path.join(input_dir, final_output_name)

        logger.info(f"\n--- Processing item: {item_name} ---")

        try:
            # Step 1: Compress to .7z with password
            logger.info("Step 1: 7z primary compression...")
            original_cwd = os.getcwd()
            os.chdir(input_dir) # Change CWD to input_dir for relative paths in archive

            cmd_7z = [
                "7z", "a", "-t7z",
                f"-p{password}",
                "-y", # Assume yes to all queries
                os.path.basename(sevenz_temp_path), # Output archive name relative to new CWD
                item_name # Item to compress relative to new CWD (this is the original file/folder name)
            ]
            subprocess.run(cmd_7z, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Successfully compressed to {os.path.basename(sevenz_temp_path)}")

            # Step 2: Rename .7z to .7删z
            logger.info("Step 2: Renaming .7z to .7删z...")
            os.rename(sevenz_temp_path, renamed_sevenz_path)
            logger.info(f"Renamed to {os.path.basename(renamed_sevenz_path)}")

            # Step 3: Compress .7删z to .zip (no encryption)
            logger.info("Step 3: ZIP secondary compression...")
            # zip command also works relative to current working directory
            cmd_zip = [
                "zip", "-q",
                os.path.basename(zip_temp_path), # Output zip name relative to new CWD
                os.path.basename(renamed_sevenz_path) # Item to zip relative to new CWD
            ]
            subprocess.run(cmd_zip, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Successfully secondary compressed to {os.path.basename(zip_temp_path)}")

            # Clean up intermediate .7删z file
            logger.info("Cleaning up intermediate .7删z file...")
            os.remove(renamed_sevenz_path)
            logger.info("Cleaned temporary file.")

            # Step 4: Rename .zip to .z删ip
            logger.info("Step 4: Final renaming .zip to .z删ip...")
            os.rename(zip_temp_path, final_output_path)
            logger.info(f"Final renamed to {os.path.basename(final_output_path)}")

            successful_items.append(item_name)
            logger.info(f"Item {item_name} processed successfully.")

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.cmd}\nStdout: {e.stdout.decode().strip()}\nStderr: {e.stderr.decode().strip()}"
            failed_items.append((item_name, error_msg))
            logger.error(f"Processing failed for {item_name}: {error_msg}")
        except Exception as e:
            error_msg = f"An unexpected error occurred: {type(e).__name__} - {e}"
            failed_items.append((item_name, error_msg))
            logger.error(f"Processing failed for {item_name}: {error_msg}")
        finally:
            os.chdir(original_cwd) # Always return to original working directory
            # Ensure cleanup of any remaining temp files in case of error
            for temp_file_path in [sevenz_temp_path, renamed_sevenz_path, zip_temp_path]:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logger.warning(f"Cleaned up leftover temp file: {os.path.basename(temp_file_path)}")
                    except OSError as e:
                        logger.error(f"Could not delete leftover temp file {os.path.basename(temp_file_path)}: {e}")

    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="Item Double Compression Report",
        total_processed=len(items_to_process),
        success_files=successful_items,
        error_files=failed_items,
        duration=duration
    )
    logger.info("All items processed!")


def decode_folders_with_double_decompression(input_dir: str, output_dir: str, password: str = "1111") -> None:
    """
    Decodes and double-decompresses files in the input_dir that have a .z删ip extension.
    Processes each file:
    1. Renames .z删ip to .zip.
    2. Decompresses the .zip file to get .7删z.
    3. Renames .7删z to .7z.
    4. Decompresses the .7z file with a password to restore original content.
       Crucially, it determines the actual original filename/foldername from the 7z archive
       to ensure correct handling of nested directories.
    5. Fixes nested directory structures if present (e.g., folder/folder).
    6. Cleans up all intermediate files, keeping only the original .z删ip and restored content.

    Args:
        input_dir (str): The directory containing the encoded .z删ip files.
        output_dir (str): The directory where decoded content will be extracted.
        password (str): The password for the inner 7z decompression (default: "1111").
    """
    logger.info(f"Starting double decompression and decoding of files in: {input_dir} to {output_dir}")

    # Check for required external commands with OS-specific messages
    if not _check_command_exists("unzip"):
        _log_missing_command_error("unzip")
        return
    if not _check_command_exists("7z"):
        _log_missing_command_error("7z")
        return

    os.makedirs(output_dir, exist_ok=True)

    encoded_files = [f for f in os.listdir(input_dir) if f.endswith(".z删ip")]
    if not encoded_files:
        logger.warning(f"No encoded files (with .z删ip extension) found in '{input_dir}' for processing.")
        return

    successful_files = []
    failed_files = []
    start_time = time.time()

    for file_name in tqdm(encoded_files, desc="Decoding Files"):
        full_zsanip_path = os.path.join(input_dir, file_name)
        
        # The .z删ip filename (e.g., "my_document" from "my_document.z删ip")
        # is the base name used for intermediate archives.
        item_base_name_from_zsanip = Path(file_name).stem 

        # Define intermediate file paths based on this item_base_name
        temp_zip_name = f"{item_base_name_from_zsanip}.zip"
        temp_7san_z_name = f"{item_base_name_from_zsanip}.7删z"
        temp_7z_name = f"{item_base_name_from_zsanip}.7z"

        temp_zip_path = os.path.join(input_dir, temp_zip_name)
        temp_7san_z_path = os.path.join(input_dir, temp_7san_z_name)
        temp_7z_path = os.path.join(input_dir, temp_7z_name)

        # Variable to store the actual original name inside the 7z archive
        # This will be the name of the file (e.g., "my_document.pdf") or folder (e.g., "my_folder/")
        extracted_original_content_name = None

        logger.info(f"\n--- Starting to process file: {file_name} ---")

        try:
            # Step 1: Copy and rename .z删ip to .zip
            logger.info(f"Step 1: Copying and renaming .z删ip to .zip -> {os.path.basename(temp_zip_path)}")
            shutil.copy2(full_zsanip_path, temp_zip_path) # Copy to avoid modifying original .z删ip in place

            # Step 2: Decompress ZIP to get .7删z
            logger.info("Step 2: Decompressing ZIP...")
            cmd_unzip = ["unzip", "-qo", temp_zip_path, "-d", input_dir]
            subprocess.run(cmd_unzip, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("ZIP decompression successful.")

            # Check if .7删z file was extracted
            if not os.path.exists(temp_7san_z_path):
                raise FileNotFoundError(f"Expected intermediate .7删z file not found: {temp_7san_z_path}")

            # Step 3: Rename .7删z to .7z
            logger.info(f"Step 3: Renaming .7删z to .7z -> {os.path.basename(temp_7z_path)}")
            os.rename(temp_7san_z_path, temp_7z_path)

            # Step 4a: List contents of 7z to get the original item name
            logger.info("Step 4a: Listing 7z archive contents to find original item name...")
            cmd_7z_list = ["7z", "l", temp_7z_path]
            result = subprocess.run(cmd_7z_list, capture_output=True, text=True, check=True)
            
            # Parse 7z list output to find the item name (e.g., "my_file.pdf" or "my_folder/")
            lines = result.stdout.splitlines()
            for line in lines:
                if 'Name' in line and 'Size' in line: # Header line
                    continue
                if '---' in line: # Separator line
                    continue
                if not line.strip(): # Empty line
                    continue
                
                # Extract the name, usually the last part of the line after all stats
                parts = line.strip().split()
                if len(parts) > 5: # Assuming typical 7z list output columns (Size, Packed, Attr, Modified, Name)
                    # The name is usually the last token, but can contain spaces.
                    extracted_original_content_name = ' '.join(parts[4:]) 
                    break
            
            if not extracted_original_content_name:
                raise ValueError("Could not determine original item name from 7z archive listing.")
            logger.info(f"Detected original item name inside archive: {extracted_original_content_name}")


            # Step 4b: Decompress 7Z with password to restore original content
            logger.info(f"Step 4b: Decompressing 7Z (password:{password}) -> Output directory: {output_dir}")
            cmd_7z_extract = [
                "7z", "x",
                f"-p{password}",
                f"-o{output_dir}", # Extract directly to output_dir
                "-y", # Assume yes to all queries
                temp_7z_path
            ]
            subprocess.run(cmd_7z_extract, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("7Z decompression successful.")

            # Step 5: Fix nested directory structure (if 7z extracted a folder/folder)
            # This applies if a directory was compressed and 7z put it into a folder of the same name.
            # E.g., if original was "my_folder", and it extracted to "output_dir/my_folder/my_folder".
            
            # Determine the top-level item extracted into output_dir based on original content name
            # If extracted_original_content_name is "my_file.pdf", then top_level_extracted_dir_name is "my_file.pdf"
            # If extracted_original_content_name is "my_folder/", then top_level_extracted_dir_name is "my_folder"
            top_level_extracted_item_name_in_output = extracted_original_content_name.strip(os.sep).split(os.sep)[0]
            full_extracted_path_in_output = os.path.join(output_dir, top_level_extracted_item_name_in_output)

            # Check if it's a directory and contains a nested directory of the same name
            potential_nested_folder_path = os.path.join(full_extracted_path_in_output, top_level_extracted_item_name_in_output)
            
            # This fix specifically targets "folder/folder" scenario
            if os.path.isdir(potential_nested_folder_path) and os.path.isdir(full_extracted_path_in_output):
                logger.info(f"Step 5: Found potential nested directory: {potential_nested_folder_path}. Fixing structure...")
                source_dir = potential_nested_folder_path
                destination_dir = full_extracted_path_in_output
                
                # Move contents from nested path to its parent
                for item in os.listdir(source_dir):
                    shutil.move(os.path.join(source_dir, item), destination_dir)
                shutil.rmtree(source_dir) # Remove the now empty nested directory
                logger.info("Removed redundant directory level.")
            else:
                logger.debug("No 'folder/folder' nested directory structure found, skipping nested fix.")
            
            successful_files.append(file_name)
            logger.info(f"File {file_name} processed successfully.")

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {e.cmd}\nStdout: {e.stdout.decode().strip()}\nStderr: {e.stderr.decode().strip()}"
            failed_files.append((file_name, error_msg))
            logger.error(f"Processing failed for {file_name}: {error_msg}")
        except FileNotFoundError as e:
            error_msg = f"Missing intermediate file: {e}"
            failed_files.append((file_name, error_msg))
            logger.error(f"Processing failed for {file_name}: {error_msg}")
        except Exception as e:
            error_msg = f"An unexpected error occurred: {type(e).__name__} - {e}"
            failed_files.append((file_name, error_msg))
            logger.error(f"Processing failed for {file_name}: {error_msg}")
        finally:
            # Clean up all intermediate files
            for temp_file_path in [temp_zip_path, temp_7san_z_path, temp_7z_path]:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logger.info(f"Cleaned up intermediate file: {os.path.basename(temp_file_path)}")
                    except OSError as e:
                        logger.error(f"Could not delete intermediate file {os.path.basename(temp_file_path)}: {e}")
            
            # If the process failed mid-way and created a partial folder/file, try to clean it
            if file_name in [f[0] for f in failed_files] and extracted_original_content_name: # Only if this specific file failed
                # Determine the top-level item that would have been extracted
                top_level_extracted_item_name_in_output = extracted_original_content_name.strip(os.sep).split(os.sep)[0]
                potential_partial_output = os.path.join(output_dir, top_level_extracted_item_name_in_output)
                
                if os.path.exists(potential_partial_output):
                    try:
                        if os.path.isdir(potential_partial_output):
                            shutil.rmtree(potential_partial_output)
                        else:
                            os.remove(potential_partial_output)
                        logger.warning(f"Cleaned up partial output: {os.path.basename(potential_partial_output)}")
                    except OSError as e:
                        logger.error(f"Could not delete partial output {os.path.basename(potential_partial_output)}: {e}")


    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="Item Double Decompression Report",
        total_processed=len(encoded_files),
        success_files=successful_files,
        error_files=failed_files,
        duration=duration
    )
    logger.info("All files processed! Final directory structure optimized.")