import os
import shutil
import logging
import time
from tqdm import tqdm
from pathlib import Path
import zipfile
import py7zr

from modules import report_generator
    
logger = logging.getLogger(__name__)

def encode_folders_with_double_compression(input_dir: str, password: str = "1111") -> None:
    logger.info(f"Starting double compression (Python libraries) of items in: {input_dir}")

    items_to_process = [
        f for f in os.listdir(input_dir)
        if f != "processed_files" and f != "decoded_files" and not f.startswith('.')
    ]
    
    if not items_to_process:
        logger.warning(f"No files or folders found in '{input_dir}' for processing (excluding hidden files and specific directories).")
        return

    successful_items = []
    failed_items = []
    start_time_total = time.time()

    for item_name in tqdm(items_to_process, desc="Encoding Items"):
        full_item_path = os.path.join(input_dir, item_name)

        item_base_name_for_archive = Path(item_name).stem if os.path.isfile(full_item_path) else item_name
        
        sevenz_temp_name = f"{item_base_name_for_archive}.7z"
        renamed_sevenz_name = f"{item_base_name_for_archive}.7删z"
        zip_temp_name = f"{item_base_name_for_archive}.zip"
        final_output_name = f"{item_base_name_for_archive}.z删ip"

        sevenz_temp_path = os.path.join(input_dir, sevenz_temp_name)
        renamed_sevenz_path = os.path.join(input_dir, renamed_sevenz_name)
        zip_temp_path = os.path.join(input_dir, zip_temp_name)
        final_output_path = os.path.join(input_dir, final_output_name)

        logger.info(f"\n--- Processing item for encoding: {item_name} ---")

        try:
            # Step 1: Compress to .7z with password using py7zr
            logger.info(f"Step 1: 7z primary compression with py7zr for '{item_name}'...")
            with py7zr.SevenZipFile(sevenz_temp_path, 'w', password=password) as archive:
                if os.path.isdir(full_item_path):
                    # arcname ensures the folder is stored with its name as the root in the archive
                    archive.writeall(full_item_path, arcname=item_name) 
                else: # it's a file
                    # arcname ensures the file is stored with its name at the root of the archive
                    archive.write(full_item_path, arcname=item_name) 
            logger.info(f"Successfully compressed '{item_name}' to '{os.path.basename(sevenz_temp_path)}'")

            # Step 2: Rename .7z to .7删z
            logger.info(f"Step 2: Renaming '{os.path.basename(sevenz_temp_path)}' to '{os.path.basename(renamed_sevenz_name)}'...")
            os.rename(sevenz_temp_path, renamed_sevenz_path)
            logger.info(f"Renamed to '{os.path.basename(renamed_sevenz_name)}'")

            # Step 3: Compress .7删z to .zip (no encryption) using zipfile
            logger.info(f"Step 3: ZIP secondary compression for '{os.path.basename(renamed_sevenz_name)}' with zipfile...")
            with zipfile.ZipFile(zip_temp_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                # Add the renamed_sevenz_file, using its basename as the name within the ZIP
                zf.write(renamed_sevenz_path, arcname=os.path.basename(renamed_sevenz_name))
            logger.info(f"Successfully secondary compressed to '{os.path.basename(zip_temp_path)}'")

            # Clean up intermediate .7删z file
            logger.info(f"Cleaning up intermediate file: '{os.path.basename(renamed_sevenz_name)}'...")
            os.remove(renamed_sevenz_path)
            logger.info("Cleaned temporary .7删z file.")

            # Step 4: Rename .zip to .z删ip
            logger.info(f"Step 4: Final renaming '{os.path.basename(zip_temp_path)}' to '{os.path.basename(final_output_name)}'...")
            os.rename(zip_temp_path, final_output_path)
            logger.info(f"Final renamed to '{os.path.basename(final_output_name)}'")

            successful_items.append(item_name)
            logger.info(f"Item '{item_name}' processed successfully for encoding.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during encoding of '{item_name}': {type(e).__name__} - {e}"
            failed_items.append((item_name, error_msg))
            logger.error(error_msg, exc_info=True) # Log with traceback for debugging
        finally:
            # Ensure cleanup of any remaining temp files from this item's processing
            for temp_file_path in [sevenz_temp_path, renamed_sevenz_path, zip_temp_path]:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                        logger.warning(f"Cleaned up leftover temp file from encoding: '{os.path.basename(temp_file_path)}'")
                    except OSError as e_clean:
                        logger.error(f"Could not delete leftover temp file '{os.path.basename(temp_file_path)}': {e_clean}")

    duration_total = time.time() - start_time_total
    if report_generator:
        report_generator.generate_report(
            report_title="Item Double Compression Report (Python Libraries)",
            total_processed=len(items_to_process),
            success_files=successful_items,
            error_files=failed_items,
            duration=duration_total
        )
    else:
        logger.info("Report generation skipped as 'report_generator' module was not found.")
    logger.info("All items processed for encoding!")


def decode_folders_with_double_decompression(input_dir: str, output_dir: str, password: str = "1111") -> None:
    # output_dir parameter is kept for signature consistency but will be ignored for extraction path.
    # Extraction will now happen into input_dir.
    logger.info(f"Starting double decompression (Python libraries) of files in '{input_dir}'. Decoded files will be placed in '{input_dir}'.")
    
    encoded_files = [f for f in os.listdir(input_dir) if f.endswith(".z删ip")]
    if not encoded_files:
        logger.warning(f"No encoded files (with .z删ip extension) found in '{input_dir}' for processing.")
        return

    successful_files = []
    failed_files = []
    start_time_total = time.time()

    for file_name in tqdm(encoded_files, desc="Decoding Files"):
        full_zsanip_path = os.path.join(input_dir, file_name)
        item_base_name_from_zsanip = Path(file_name).stem 

        temp_zip_name = f"{item_base_name_from_zsanip}.zip"
        # This is the expected name of the .7删z file *inside* the .zip archive
        # and also the name of the file when extracted.
        name_of_7sanz_inside_zip = f"{item_base_name_from_zsanip}.7删z"
        
        temp_zip_path = os.path.join(input_dir, temp_zip_name)
        # Path where the .7删z file will be extracted from the zip
        extracted_7sanz_path = os.path.join(input_dir, name_of_7sanz_inside_zip)
        # Path for the .7z file after renaming
        temp_7z_path = os.path.join(input_dir, f"{item_base_name_from_zsanip}.7z")
        
        extracted_original_content_name = None 
        logger.info(f"\n--- Starting to process file for decoding: {file_name} ---")

        try:
            # Step 1: Copy .z删ip and rename to .zip
            logger.info(f"Step 1: Copying '{file_name}' and renaming to '{os.path.basename(temp_zip_path)}'...")
            shutil.copy2(full_zsanip_path, temp_zip_path)

            # Step 2: Decompress ZIP to get .7删z using zipfile
            logger.info(f"Step 2: Decompressing '{os.path.basename(temp_zip_path)}' with zipfile...")
            with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                # Ensure the specific .7删z file is in the zip before extracting
                if name_of_7sanz_inside_zip not in zf.namelist():
                    raise FileNotFoundError(f"'{name_of_7sanz_inside_zip}' not found inside '{temp_zip_path}'. Available: {zf.namelist()}")
                # Extracts to input_dir/name_of_7sanz_inside_zip
                zf.extract(name_of_7sanz_inside_zip, path=input_dir) 
            logger.info(f"ZIP decompression successful, extracted '{name_of_7sanz_inside_zip}' to '{input_dir}'")

            if not os.path.exists(extracted_7sanz_path): # Double check
                 raise FileNotFoundError(f"Expected intermediate file not found after ZIP extraction: '{extracted_7sanz_path}'")

            # Step 3: Rename .7删z to .7z
            logger.info(f"Step 3: Renaming '{name_of_7sanz_inside_zip}' to '{os.path.basename(temp_7z_path)}'...")
            os.rename(extracted_7sanz_path, temp_7z_path)

            # Step 4a: List contents of 7z to get the original item name using py7zr
            # This step is still useful to know the name of the item that will be extracted,
            # even if we don't use it for nested folder fixing later.
            logger.info(f"Step 4a: Getting original item name from '{os.path.basename(temp_7z_path)}' with py7zr...")
            with py7zr.SevenZipFile(temp_7z_path, 'r', password=password) as archive:
                archived_names = archive.getnames()
                if not archived_names:
                    raise ValueError(f"7z archive '{os.path.basename(temp_7z_path)}' is empty or names could not be read.")
                extracted_original_content_name = archived_names[0]
                if extracted_original_content_name.endswith('/') or extracted_original_content_name.endswith('\\'):
                     extracted_original_content_name = extracted_original_content_name[:-1]

            if not extracted_original_content_name: 
                raise ValueError(f"Could not determine original item name from 7z archive '{os.path.basename(temp_7z_path)}'.")
            logger.info(f"Detected original item name inside archive: '{extracted_original_content_name}'")

            # Step 4b: Decompress 7Z with password to restore original content using py7zr
            # MODIFIED: Extract directly to input_dir
            logger.info(f"Step 4b: Decompressing '{os.path.basename(temp_7z_path)}' with py7zr (password:****) to '{input_dir}'...")
            with py7zr.SevenZipFile(temp_7z_path, 'r', password=password) as archive:
                archive.extractall(path=input_dir) # MODIFIED: Changed output_dir to input_dir
            logger.info("7Z decompression successful.")

            # Step 5: REMOVED - Nested directory structure fixing is no longer needed as per user request.
            logger.info("Step 5: Nested directory fixing skipped as per user request.")
            
            successful_files.append(file_name)
            logger.info(f"File '{file_name}' processed successfully for decoding.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during decoding of '{file_name}': {type(e).__name__} - {e}"
            failed_files.append((file_name, error_msg))
            logger.error(error_msg, exc_info=True) # Log with traceback
        finally:
            # Clean up intermediate files from input_dir
            for temp_file_path_cleanup in [temp_zip_path, extracted_7sanz_path, temp_7z_path]:
                if os.path.exists(temp_file_path_cleanup):
                    try:
                        os.remove(temp_file_path_cleanup)
                        logger.info(f"Cleaned up intermediate file from decoding: '{os.path.basename(temp_file_path_cleanup)}'")
                    except OSError as e_clean:
                        logger.error(f"Could not delete intermediate file '{os.path.basename(temp_file_path_cleanup)}': {e_clean}")
            
            # Cleanup partial extraction in input_dir if this file failed
            # This part needs to be careful as input_dir is now also the extraction target.
            # We only want to remove the specific item that was being extracted if it failed.
            if file_name in [f[0] for f in failed_files] and extracted_original_content_name:
                # The item that would have been created in input_dir
                potential_partial_output = os.path.join(input_dir, extracted_original_content_name)
                if os.path.exists(potential_partial_output):
                    # Check if it's not one of the original .z删ip files or other essential files
                    if not potential_partial_output.endswith(".z删ip") and potential_partial_output != full_zsanip_path:
                        logger.warning(f"Attempting to clean up partial output due to failure: '{potential_partial_output}'")
                        try:
                            if os.path.isdir(potential_partial_output): shutil.rmtree(potential_partial_output)
                            else: os.remove(potential_partial_output)
                            logger.info(f"Cleaned up partial output: '{os.path.basename(potential_partial_output)}'")
                        except OSError as e_clean:
                            logger.error(f"Could not delete partial output '{os.path.basename(potential_partial_output)}': {e_clean}")
                        
    duration_total = time.time() - start_time_total
    if report_generator: # Check if report_generator was successfully imported
        report_generator.generate_report(
            report_title="Item Double Decompression Report (Python Libraries)",
            total_processed=len(encoded_files),
            success_files=successful_files,
            error_files=failed_files,
            duration=duration_total
        )
    else:
        logger.info("Report generation skipped as 'report_generator' module was not found.")
    logger.info("All files processed for decoding!")