import os
import re
import shutil
import time
import unicodedata
import logging
from tqdm import tqdm
from pypinyin import pinyin, Style

try:
    from modules import report_generator
except ImportError:
    import report_generator

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def normalize_str(s: str) -> str:
    """
    Normalizes a string using NFC (Normalization Form Canonical Composition).
    Args:
        s (str): The input string.
    Returns:
        str: The normalized string.
    """
    return unicodedata.normalize('NFC', s)

def clean_name(filename: str) -> str:
    """
    Cleans a filename by removing author names in brackets, extensions,
    and truncating at the first occurrence of numbers or specific symbols.
    Compresses multiple spaces into a single space.
    Args:
        filename (str): The original filename.
    Returns:
        str: The cleaned filename.
    """
    # Remove author name (content in []) and extension
    if filename.startswith('['):
        try:
            idx = filename.index(']') + 1
            filename = filename[idx:].strip()
        except ValueError:
            pass # No closing bracket found, keep original
    filename = os.path.splitext(filename)[0]
    filename = normalize_str(filename)

    # Find the position of the first digit or [, ], (, ), @ symbol, and truncate the string
    cut_pos = len(filename)  # Default to no truncation
    for ch in '0123456789[]()@':
        pos = filename.find(ch)
        if pos != -1 and pos < cut_pos:
            cut_pos = pos
    filename = filename[:cut_pos].strip()

    # Compress multiple spaces into a single space
    filename = re.sub(r'\s+', ' ', filename)
    return filename

def _generate_new_name(original_name: str) -> str:
    """
    Generates a standardized filename (internal function).
    Args:
        original_name (str): Original filename
    Returns:
        str: New filename in the format "Prefix-OriginalName"
    Processing logic:
        1. Extracts the first character (Chinese or English letter).
        2. Converts Chinese characters to Pinyin initials.
        3. Cleans up special prefixes.
    Example:
        "测试文件.pdf" → "C-测试文件.pdf"
        "2024报告.txt" → "B-2024报告.txt"
    """
    if not isinstance(original_name, str) or len(original_name) == 0:
        logger.error(f"Invalid original name: {original_name}")
        return original_name

    # Clean up old prefixes
    clean_name = re.sub(r'^[A-Za-z\u4e00-\u9fff]-', '', original_name)

    # Extract the first character
    first_char_match = re.search(r'([\u4e00-\u9fff]|[A-Za-z])', clean_name)
    if not first_char_match:
        logger.warning(f"Could not generate prefix for: {original_name}")
        return original_name

    # Generate Pinyin initial (with error handling)
    try:
        first_char = first_char_match.group()
        if re.match(r'[\u4e00-\u9fff]', first_char):
            prefix = pinyin(first_char, style=Style.FIRST_LETTER)[0][0].upper()
        else:
            prefix = first_char.upper()
    except Exception as e:
        logger.error(f"Pinyin conversion failed: {first_char} - {str(e)}")
        return original_name

    return f"{prefix}-{clean_name}"

def delete_filename_chars(input_dir: str, char: str) -> None:
    """
    Deletes specific characters from filenames in the specified directory.
    Args:
        input_dir (str): The directory containing the files.
        char (str): The character (or regex pattern) to delete from filenames.
    """
    logger.info(f"Starting to delete character '{char}' from filenames in: {input_dir}")
    processed_count = 0
    for f in tqdm(os.listdir(input_dir), desc="Deleting Chars"):
        old_path = os.path.join(input_dir, f)
        if os.path.isfile(old_path) or os.path.isdir(old_path): # Process both files and directories
            new_name = re.sub(char, '', f) # Use re.sub for regex support
            if new_name != f: # Only rename if a change occurred
                new_path = os.path.join(input_dir, new_name)
                counter = 1
                original_new_name = new_name
                while os.path.exists(new_path) and new_path != old_path: # Handle conflicts
                    base, ext = os.path.splitext(original_new_name)
                    new_name = f"{base}_{counter}{ext}"
                    new_path = os.path.join(input_dir, new_name)
                    counter += 1
                try:
                    os.rename(old_path, new_path)
                    logger.info(f"Renamed: {f} -> {new_name}")
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to rename {f}: {e}")
    logger.info(f"Deletion of characters complete. Processed {processed_count} items.")


def rename_items(input_dir: str, mode: str) -> None:
    """
    Batch rename files/directories in the specified directory.
    Args:
        input_dir (str): The directory containing the files/directories to rename.
        mode (str): Processing mode, optional values:
            'both'    : Process both files and directories.
            'folders' : Process directories only.
            'files'   : Process files only.
    Features:
        - Automatically handles filename conflicts (appends a serial number).
        - Retains file extensions.
        - Supports interruption recovery (atomic renaming).
    """
    valid_modes = ['both', 'folders', 'files']
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode}")

    logger.info(f"Starting batch renaming operation in '{input_dir}' for mode: '{mode}'")
    items = []
    for name in os.listdir(input_dir):
        path = os.path.join(input_dir, name)
        if not os.path.exists(path):
            logger.warning(f"Path does not exist: {path}. Skipping.")
            continue

        if mode in ['both', 'folders'] and os.path.isdir(path):
            items.append(('folder', name))
        elif mode in ['both', 'files'] and os.path.isfile(path):
            items.append(('file', name))

    renamed_count = 0
    with tqdm(items, desc=f"Renaming {mode}") as pbar:
        for item_type, name in pbar:
            old_path = os.path.join(input_dir, name)

            new_base = _generate_new_name(name)
            if not isinstance(new_base, str) or new_base == name: # Skip if name generation failed or no change
                logger.info(f"Skipping '{name}': new name not generated or no change.")
                continue

            # Handle file extension for files
            if item_type == 'file':
                base_part, ext = os.path.splitext(new_base)
                if not ext: # If new name loses extension, re-add original
                    original_ext = os.path.splitext(name)[1]
                    new_base += original_ext
                new_name = new_base
            else: # For folders, new_base is the final new_name
                new_name = new_base

            new_path = os.path.join(input_dir, new_name)

            # Conflict resolution (try up to 100 times)
            counter = 1
            original_new_name_for_conflict = new_name # Store the initially desired new name for conflict resolution
            while os.path.exists(new_path) and new_path != old_path:
                base, ext = os.path.splitext(original_new_name_for_conflict) if item_type == 'file' else (original_new_name_for_conflict, '')
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(input_dir, new_name)
                counter += 1
                if counter > 100: # Prevent infinite loop for extreme conflicts
                    logger.error(f"Too many conflicts for '{name}', skipping.")
                    new_name = None # Mark for skipping
                    break

            if new_name is None: # If conflict resolution failed
                continue

            try:
                os.rename(old_path, new_path)
                renamed_count += 1
                logger.info(f"Renamed: {name} → {new_name}")
                pbar.set_postfix_str(f"Latest: {name[:15]} → {new_name[:15]}")
            except Exception as e:
                logger.error(f"Failed to rename '{name}' to '{new_name}': {e}")

    logger.info(f"Batch renaming complete! Processed {renamed_count} items.")


def flatten_directories(input_dir: str) -> None:
    """
    Directory flattening process in the specified input directory.
    Features:
        1. Extracts all files from subdirectories to the root directory.
        2. Deletes empty subdirectories (including nested ones).
        3. Automatically handles filename conflicts (appends a serial number).
    Risks:
        - May cause filename conflicts.
        - Irreversible operation (directory deletion).
    Args:
        input_dir (str): The directory to flatten.
    """
    logger.info(f"Starting directory flattening operation in: {input_dir}")
    moved_files = 0

    # Get a list of all direct subdirectories in the input directory
    direct_subdirs = [os.path.join(input_dir, name) for name in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, name))]

    if not direct_subdirs:
        logger.info(f"No subdirectories found in '{input_dir}' to flatten.")
        return

    # Phase 1: Move all files from subdirectories to the input_dir
    for dir_path in tqdm(direct_subdirs, desc="Moving files from subdirectories"):
        # os.walk yields (dirpath, dirnames, filenames)
        # topdown=True is default, but explicitly setting it for clarity
        for root, _, files in os.walk(dir_path, topdown=True):
            for file in files:
                src = os.path.join(root, file)
                dest = os.path.join(input_dir, file)

                # Handle filename conflicts
                counter = 1
                base, ext = os.path.splitext(file)
                original_dest_name = file # Keep original name for conflict resolution
                while os.path.exists(dest):
                    new_name_for_conflict = f"{base}_{counter}{ext}"
                    dest = os.path.join(input_dir, new_name_for_conflict)
                    counter += 1
                    if counter > 1000: # Safety break for extreme conflicts
                        logger.error(f"Too many conflicts for file '{file}' in '{root}', skipping.")
                        dest = None # Mark as skipped
                        break
                
                if dest is None: # If conflict resolution failed
                    continue

                try:
                    shutil.move(src, dest)
                    moved_files += 1
                    logger.info(f"Moved file '{os.path.basename(src)}' to '{os.path.basename(dest)}'")
                except Exception as e:
                    logger.error(f"Failed to move file '{src}' to '{dest}': {e}")
        
    logger.info(f"Finished moving files. Moved {moved_files} files.")

    # Phase 2: Recursively delete all empty subdirectories from the bottom up
    logger.info(f"Starting recursive cleanup of empty subdirectories in: {input_dir}")
    deleted_dirs_count = 0
    # os.walk with topdown=False traverses directories from bottom-up
    for root, dirs, files in os.walk(input_dir, topdown=False):
        # Only consider directories that are not the input_dir itself
        if root == input_dir:
            continue

        try:
            # Check if the current directory is empty (no files and no subdirectories left)
            if not os.listdir(root):
                shutil.rmtree(root)
                deleted_dirs_count += 1
                logger.info(f"Successfully deleted empty directory: {root}")
            else:
                logger.debug(f"Directory '{root}' is not empty, skipping deletion.")
        except OSError as e:
            logger.error(f"Failed to delete directory '{root}': {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting directory '{root}': {e}")

    logger.info(f"Recursive cleanup complete. Deleted {deleted_dirs_count} empty subdirectories.")
    logger.info(f"Directory flattening operation finished.")


def add_filename_prefix(input_dir: str, prefix: str, processed_files: list = None) -> None:
    """
    Adds a prefix to filenames in the specified directory.
    Args:
        input_dir (str): The directory containing the files.
        prefix (str): The prefix to add.
        processed_files (list, optional): A list of files that have already been processed
                                         (e.g., by extract_numbers_in_filenames) to skip.
                                         Defaults to None.
    Features:
        - Only affects PDF/TXT/EPUB files and directories.
        - Automatically skips files that already have the prefix.
    """
    logger.info(f"Starting to add prefix '{prefix}' to items in: {input_dir}")

    try:
        files_in_dir = os.listdir(input_dir)
    except Exception as e:
        logger.error(f"Could not read directory '{input_dir}': {e}")
        return

    target_files = []
    for f in files_in_dir:
        full_path = os.path.join(input_dir, f)
        if f.startswith(prefix): # Skip if already has prefix
            logger.info(f"Skipping '{f}': already has prefix '{prefix}'.")
            continue
        
        # Check if it's a target file type or a directory
        if (os.path.isfile(full_path) and f.lower().endswith(('.pdf', '.txt', '.epub'))) or os.path.isdir(full_path):
            # If processed_files list is provided, check if the file was already processed
            if processed_files and f in processed_files:
                logger.info(f"Skipping '{f}': already processed by another operation.")
                continue
            target_files.append(f)

    if not target_files:
        logger.info("No matching files found or all files already have the prefix.")
        return

    with tqdm(target_files, desc="Adding Prefix") as pbar:
        for file in pbar:
            src = os.path.join(input_dir, file)
            new_name = f"{prefix}{file}"
            dest = os.path.join(input_dir, new_name)

            # Handle conflicts
            counter = 1
            original_new_name_for_conflict = new_name
            while os.path.exists(dest) and dest != src: # Ensure we don't try to rename to itself if it already exists
                base, ext = os.path.splitext(original_new_name_for_conflict) if os.path.isfile(src) else (original_new_name_for_conflict, '')
                new_name = f"{base}_{counter}{ext}"
                dest = os.path.join(input_dir, new_name)
                counter += 1
                if counter > 100: # Safety break
                    logger.error(f"Too many conflicts for '{file}', skipping prefix addition.")
                    new_name = None
                    break
            
            if new_name is None:
                continue

            try:
                os.rename(src, dest)
                logger.info(f"Successfully renamed: {file} → {new_name}")
            except Exception as e:
                logger.error(f"Failed to add prefix to '{file}': {e}")

    logger.info(f"Prefix addition complete! Processed {len(target_files)} files (PDF/TXT/EPUB/FOLDER).")

def extract_numbers_in_filenames(input_dir: str) -> list:
    """
    Extracts numbers from filenames in the specified directory and renames them.
    Args:
        input_dir (str): The directory containing the files.
    Returns:
        list: A list of filenames that were successfully processed.
    """
    logger.info(f"Starting to extract numbers from filenames in: {input_dir}")
    processed_files = []
    failed_files = []
    skipped_files = []
    start_time = os.path.getmtime(input_dir) # Using directory modification time as a proxy for start time

    # Get all files (case-insensitive)
    all_files_in_dir = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

    with tqdm(all_files_in_dir, desc="Processing Files", unit="file") as pbar:
        for filename in pbar:
            src_path = os.path.join(input_dir, filename)

            # Skip purely numeric filenames (e.g., "123.pdf")
            base_without_ext = os.path.splitext(filename)[0]
            if re.fullmatch(r'^\d+$', base_without_ext):
                skipped_files.append(filename)
                logger.info(f"Skipping purely numeric file: {filename}")
                continue

            # Extract all numbers and hyphens
            numbers = re.sub(r'[^0-9-]', '', filename)
            # Remove leading and trailing hyphens
            numbers = numbers.lstrip('-').rstrip('-')

            # Check if it contains any numbers
            if not re.search(r'\d', numbers):
                skipped_files.append(filename)
                logger.warning(f"No numbers found in filename: {filename}. Skipping.")
                continue

            # Determine original extension
            _, original_ext = os.path.splitext(filename)

            # Generate base filename
            base_name = f"{numbers}{original_ext}"
            dest_path = os.path.join(input_dir, base_name)

            # Handle filename conflicts
            counter = 1
            original_dest_name_for_conflict = base_name
            while os.path.exists(dest_path) and dest_path != src_path:
                base, ext = os.path.splitext(original_dest_name_for_conflict)
                new_name_for_conflict = f"{base}_{counter}{ext}"
                dest_path = os.path.join(input_dir, new_name_for_conflict)
                counter += 1
                if counter > 1000: # Safety break for extreme conflicts
                    logger.error(f"Too many conflicts for '{filename}', skipping numeric extraction.")
                    dest_path = None # Mark as skipped
                    break

            if dest_path is None: # If conflict resolution failed
                failed_files.append((filename, "Conflict resolution failed"))
                continue

            try:
                os.rename(src_path, dest_path)
                processed_files.append(os.path.basename(dest_path))
                pbar.set_postfix_str(f"Latest Processed: {filename[:15]} → {os.path.basename(dest_path)[:15]}")
            except Exception as e:
                failed_files.append((filename, str(e)))
                logger.error(f"Failed to rename '{filename}': {e}")

    # Use report_generator to generate the report
    report_generator.generate_report(
        report_title="Number Extraction Report",
        total_processed=len(all_files_in_dir),
        success_files=processed_files,
        error_files=failed_files,
        duration=time.time() - start_time # Calculate duration
    )

    if skipped_files:
        logger.info("Skipped files list (purely numeric or no numbers found):")
        for f in skipped_files:
            logger.info(f"  · {f}")

    return processed_files

def reverse_rename(input_dir: str) -> None:
    """
    Reverse renaming (removes prefix) for files and directories in the specified directory.
    Processing rules:
        Format "X-filename" → "filename".
        Example: "A-report.pdf" → "report.pdf".
    Features:
        - Automatically handles name conflicts.
        - Supports both files and directories.
    Args:
        input_dir (str): The directory containing the files/directories to process.
    """
    logger.info(f"Starting reverse renaming operation in: {input_dir}")
    renamed_count = 0
    success_files = []
    error_files = []
    start_time = os.path.getmtime(input_dir) # Using directory modification time as a proxy for start time

    # Process all items (files and folders) in the input directory
    items = [name for name in os.listdir(input_dir)]

    with tqdm(items, desc="Reverse Renaming") as pbar:
        for name in pbar:
            old_path = os.path.join(input_dir, name)

            # Match format: X-xxxx (X is a single letter or Chinese character)
            match = re.match(r'^([A-Z\u4e00-\u9fff])-(.+)$', name)
            if not match:
                logger.info(f"Skipping non-matching format: {name}")
                continue

            # Generate new name (without prefix)
            new_name = match.group(2)
            new_path = os.path.join(input_dir, new_name)

            # Handle name conflicts
            counter = 1
            original_new_name_for_conflict = new_name
            while os.path.exists(new_path) and new_path != old_path:
                base, ext = os.path.splitext(original_new_name_for_conflict) if os.path.isfile(old_path) else (original_new_name_for_conflict, '')
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(input_dir, new_name)
                counter += 1
                if counter > 100: # Safety break
                    logger.error(f"Too many conflicts for '{name}', skipping reverse rename.")
                    new_name = None
                    break
            
            if new_name is None:
                error_files.append((name, "Conflict resolution failed"))
                continue

            try:
                os.rename(old_path, new_path)
                renamed_count += 1
                success_files.append(new_name)
                logger.info(f"Reverse renamed: {name} → {new_name}")
                pbar.set_postfix_str(f"Latest: {name[:15]} → {new_name[:15]}")
            except Exception as e:
                error_files.append((name, str(e)))
                logger.error(f"Failed to rename '{name}' to '{new_name}': {e}")

    # Use report_generator to generate the report
    report_generator.generate_report(
        report_title="Reverse Renaming Report",
        total_processed=len(items),
        success_files=success_files,
        error_files=error_files,
        duration=time.time() - start_time
    )

    logger.info(f"✅ Reverse renaming complete! Processed {renamed_count} items.")