import os
import re
import shutil
import time
import unicodedata
import logging
from tqdm import tqdm
from pypinyin import pinyin, Style

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
    module_logger = logging.getLogger(__name__)
    try:
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
    except Exception as e:
        module_logger.error(f"Error cleaning name for '{filename}': {e}")
        return filename # Return original on error to avoid breaking further ops

def _generate_new_name(original_name: str, module_logger: logging.Logger) -> str:
    """
    Generates a standardized filename (internal function).
    Args:
        original_name (str): Original filename
        module_logger (logging.Logger): Logger instance for logging.
    Returns:
        str: New filename in the format "Prefix-OriginalName" or original_name on error.
    """
    if not isinstance(original_name, str) or len(original_name) == 0:
        module_logger.error(f"Invalid original name provided for prefix generation: {original_name}")
        return original_name

    clean_val = re.sub(r'^[A-Za-z\u4e00-\u9fff]-', '', original_name)
    first_char_match = re.search(r'([\u4e00-\u9fff]|[A-Za-z])', clean_val)

    if not first_char_match:
        module_logger.warning(f"Could not determine first character for prefix generation from: '{clean_val}' (original: '{original_name}')")
        return original_name

    prefix = ''
    try:
        first_char = first_char_match.group(1)
        if re.match(r'[\u4e00-\u9fff]', first_char): # Chinese character
            prefix = pinyin(first_char, style=Style.FIRST_LETTER)[0][0].upper()
        elif re.match(r'[A-Za-z]', first_char): # English letter
            prefix = first_char.upper()
        else:
            module_logger.warning(f"First character '{first_char}' is not Chinese or English letter, cannot generate pinyin prefix for: {original_name}")
            return original_name
    except Exception as e:
        module_logger.error(f"Pinyin/prefix generation failed for char '{first_char_match.group(1)}' in '{original_name}': {e}")
        return original_name # Return original on error

    return f"{prefix}-{clean_val}"


def delete_filename_chars_api(input_dir: str, char_pattern: str) -> dict:
    """
    API-adapted: Deletes specific characters from filenames in the specified directory.
    Args:
        input_dir (str): The directory containing the files.
        char_pattern (str): The character (or regex pattern) to delete.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Deleting pattern '{char_pattern}' from filenames in '{input_dir}'")
    messages = []
    processed_count = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1}

    try:
        items_in_dir = os.listdir(input_dir)
    except Exception as e:
        msg = f"Could not read directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "error_count": 1}

    for item_name in tqdm(items_in_dir, desc="API Deleting Chars", unit="item", disable=True):
        old_path = os.path.join(input_dir, item_name)
        
        try:
            new_item_name_candidate = re.sub(char_pattern, '', item_name)
        except re.error as e_re:
            msg = f"Invalid regex pattern '{char_pattern}': {e_re}. Skipping item '{item_name}'."
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += 1
            overall_success = False
            continue

        if new_item_name_candidate != item_name:
            new_path_candidate = os.path.join(input_dir, new_item_name_candidate)
            
            final_new_name = new_item_name_candidate
            final_new_path = new_path_candidate
            counter = 1
            
            # Handle potential conflicts if the new name already exists
            while os.path.exists(final_new_path) and final_new_path != old_path:
                base, ext = os.path.splitext(new_item_name_candidate)
                final_new_name = f"{base}_{counter}{ext}"
                final_new_path = os.path.join(input_dir, final_new_name)
                counter += 1
                if counter > 100: # Safety break
                    msg = f"Too many name conflicts for '{item_name}' after deleting chars. Original new name: '{new_item_name_candidate}'. Skipping."
                    module_logger.error(msg)
                    messages.append(f"[ERROR] {msg}")
                    error_count += 1
                    overall_success = False
                    final_new_path = None # Indicate failure to resolve conflict
                    break
            
            if final_new_path is None:
                continue

            try:
                os.rename(old_path, final_new_path)
                msg = f"Renamed: '{item_name}' -> '{final_new_name}'"
                module_logger.info(msg)
                messages.append(f"[SUCCESS] {msg}")
                processed_count += 1
            except Exception as e_rename:
                msg = f"Failed to rename '{item_name}' to '{final_new_name}': {e_rename}"
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                error_count += 1
                overall_success = False
        else:
            messages.append(f"[INFO] No changes needed for '{item_name}'.")

    final_summary = f"Character/pattern deletion complete. Processed renames: {processed_count}, Errors: {error_count}."
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
    return {"success": overall_success, "messages": messages, "processed_count": processed_count, "error_count": error_count}


def rename_items_api(input_dir: str, mode: str) -> dict:
    """
    API-adapted: Batch rename files/directories.
    Args:
        input_dir (str): The directory.
        mode (str): 'both', 'folders', 'files'.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Renaming items in '{input_dir}', mode: '{mode}'")
    messages = []
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    overall_success = True

    valid_modes = ['both', 'folders', 'files']
    if mode not in valid_modes:
        msg = f"Invalid rename mode: {mode}. Must be one of {valid_modes}."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "renamed_count": 0, "skipped_count": 0, "error_count": 1}

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "renamed_count": 0, "skipped_count": 0, "error_count": 1}

    items_to_process = []
    try:
        for name in os.listdir(input_dir):
            path = os.path.join(input_dir, name)
            if mode == 'folders' and os.path.isdir(path):
                items_to_process.append({'type': 'folder', 'name': name, 'path': path})
            elif mode == 'files' and os.path.isfile(path):
                items_to_process.append({'type': 'file', 'name': name, 'path': path})
            elif mode == 'both':
                item_type = 'folder' if os.path.isdir(path) else 'file' if os.path.isfile(path) else None
                if item_type:
                    items_to_process.append({'type': item_type, 'name': name, 'path': path})
    except Exception as e:
        msg = f"Error listing directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "renamed_count": 0, "skipped_count": 0, "error_count": 1}


    for item_info in tqdm(items_to_process, desc=f"API Renaming {mode}", unit="item", disable=True):
        item_type, old_name, old_path = item_info['type'], item_info['name'], item_info['path']
        
        generated_name_with_prefix = _generate_new_name(old_name, module_logger)

        if generated_name_with_prefix == old_name:
            msg = f"Skipping '{old_name}': generated name is the same or generation failed."
            module_logger.info(msg)
            messages.append(f"[SKIP] {msg}")
            skipped_count +=1
            continue

        # Ensure extension is preserved for files if _generate_new_name removed it
        # _generate_new_name already cleans the prefix like 'A-' from 'A-file.txt' to 'file.txt' before making 'F-file.txt'
        # So, the main concern is if original_name had no extension and _generate_new_name produced something.
        # The logic in _generate_new_name returns 'PREFIX-cleaned_original_name_without_ext'. We must add ext.
        
        final_new_item_name = generated_name_with_prefix
        if item_type == 'file':
            _, original_ext = os.path.splitext(old_name)
            final_new_item_name = generated_name_with_prefix + original_ext
            final_new_item_name = _remove_duplicate_extension(final_new_item_name)


        new_path_candidate = os.path.join(input_dir, final_new_item_name)
        
        current_new_name_for_conflict = final_new_item_name
        current_new_path = new_path_candidate
        counter = 1

        while os.path.exists(current_new_path) and current_new_path != old_path:
            base, ext = os.path.splitext(final_new_item_name)
            current_new_name_for_conflict = f"{base}_{counter}{ext}"
            current_new_path = os.path.join(input_dir, current_new_name_for_conflict)
            counter += 1
            if counter > 100:
                msg = f"Too many name conflicts for '{old_name}' (target: '{final_new_item_name}'). Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                error_count += 1
                overall_success = False
                current_new_path = None
                break
        
        if current_new_path is None:
            continue

        try:
            os.rename(old_path, current_new_path)
            msg = f"Renamed: '{old_name}' -> '{os.path.basename(current_new_path)}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            renamed_count += 1
        except Exception as e_rename:
            msg = f"Failed to rename '{old_name}' to '{os.path.basename(current_new_path)}': {e_rename}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += 1
            overall_success = False

    final_summary = f"Batch renaming complete. Renamed: {renamed_count}, Skipped: {skipped_count}, Errors: {error_count}."
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
    return {"success": overall_success, "messages": messages, "renamed_count": renamed_count, "skipped_count": skipped_count, "error_count": error_count}


def flatten_directories_api(input_dir: str) -> dict:
    """
    API-adapted: Directory flattening process.
    Args:
        input_dir (str): The directory to flatten.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Flattening directories in '{input_dir}'")
    messages = []
    moved_files_count = 0
    deleted_dirs_count = 0
    conflict_skips = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "moved_files_count":0, "deleted_dirs_count":0, "conflict_skips":0, "error_count":1}

    # Phase 1: Move files
    # Collect all files to be moved first to avoid issues with os.walk on changing directories
    files_to_move = []
    try:
        for root, _, files in os.walk(input_dir):
            if root == input_dir:  # Don't process files already in the root
                continue
            for file_item in files:
                files_to_move.append({'src': os.path.join(root, file_item), 'name': file_item})
    except Exception as e_walk:
        msg = f"Error during initial scan of '{input_dir}': {e_walk}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "moved_files_count":0, "deleted_dirs_count":0, "conflict_skips":0, "error_count":1}


    for file_info in tqdm(files_to_move, desc="API Moving Files", unit="file", disable=True):
        src_path, original_name = file_info['src'], file_info['name']
        dest_path_candidate = os.path.join(input_dir, original_name)
        
        current_dest_name = original_name
        current_dest_path = dest_path_candidate
        counter = 1

        while os.path.exists(current_dest_path):
            # Important: if src_path is the same as current_dest_path, it means the file is already in the root.
            # This shouldn't happen with the `if root == input_dir: continue` logic, but as a safeguard:
            if os.path.samefile(src_path, current_dest_path):
                 module_logger.debug(f"File '{original_name}' is already at destination or is the same file. Skipping move.")
                 current_dest_path = None # Mark to skip move
                 break

            base, ext = os.path.splitext(original_name)
            current_dest_name = f"{base}_{counter}{ext}"
            current_dest_path = os.path.join(input_dir, current_dest_name)
            counter += 1
            if counter > 1000:
                msg = f"Too many name conflicts for file '{original_name}' from '{os.path.dirname(src_path)}'. Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg} - Conflict skip.")
                conflict_skips += 1
                error_count +=1 # Count conflict skip as an error for summary
                overall_success = False
                current_dest_path = None
                break
        
        if current_dest_path is None:
            continue

        try:
            shutil.move(src_path, current_dest_path)
            moved_files_count += 1
            messages.append(f"[SUCCESS] Moved '{original_name}' from '{os.path.dirname(src_path)}' to '{current_dest_name}' in root.")
        except Exception as e_move:
            msg = f"Failed to move file '{src_path}' to '{current_dest_path}': {e_move}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += 1
            overall_success = False
            
    messages.append(f"[INFO] File moving phase complete. Moved: {moved_files_count} files.")

    # Phase 2: Delete empty directories
    module_logger.info(f"API: Cleaning up empty subdirectories in '{input_dir}'")
    deleted_dirs_this_pass = -1 # Loop sentinel
    while deleted_dirs_this_pass != 0 : # Loop until no more empty dirs are deleted in a pass
        deleted_dirs_this_pass = 0
        # Walk from bottom up to remove nested empty directories correctly
        for root, dirs, files_in_subdir in os.walk(input_dir, topdown=False):
            if root == input_dir:
                continue # Don't try to delete the input directory itself

            is_empty = not os.listdir(root) # More direct check for emptiness

            if is_empty:
                try:
                    os.rmdir(root) # Use os.rmdir for empty dirs; shutil.rmtree for non-empty (but we expect empty)
                    deleted_dirs_count += 1
                    deleted_dirs_this_pass +=1
                    messages.append(f"[SUCCESS] Deleted empty directory: '{root}'")
                except OSError as e_rmdir: # os.rmdir raises OSError if not empty or other issues
                    # This might happen if a .DS_Store or other hidden file remains
                    msg = f"Could not delete directory '{root}': {e_rmdir}. It might not be truly empty or access denied."
                    module_logger.warning(msg) # Log as warning, might not be a critical error
                    messages.append(f"[WARN] {msg}")
                    # error_count += 1 # Optionally count this as an error
                    # overall_success = False
                except Exception as e_generic_rm:
                    msg = f"Unexpected error deleting directory '{root}': {e_generic_rm}"
                    module_logger.error(msg)
                    messages.append(f"[ERROR] {msg}")
                    error_count += 1
                    overall_success = False
    
    final_summary = (f"Directory flattening finished. Moved files: {moved_files_count}, "
                     f"Deleted empty directories: {deleted_dirs_count}, "
                     f"Conflict skips: {conflict_skips}, Other errors: {error_count}.")
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
    return {"success": overall_success, "messages": messages, "moved_files_count": moved_files_count, 
            "deleted_dirs_count": deleted_dirs_count, "conflict_skips": conflict_skips, "error_count": error_count}


def add_filename_prefix_api(input_dir: str, prefix: str, processed_files_list: list = None) -> dict:
    """
    API-adapted: Adds a prefix to filenames.
    Args:
        input_dir (str): The directory.
        prefix (str): The prefix to add.
        processed_files_list (list, optional): Files already processed to skip.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Adding prefix '{prefix}' in '{input_dir}'")
    messages = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "skipped_count": 0, "error_count": 1}

    try:
        items_in_dir = os.listdir(input_dir)
    except Exception as e:
        msg = f"Could not read directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "skipped_count": 0, "error_count": 1}

    if processed_files_list is None:
        processed_files_list = []

    target_items = []
    for item_name in items_in_dir:
        full_path = os.path.join(input_dir, item_name)
        if item_name.startswith(prefix):
            msg = f"Skipping '{item_name}': already has prefix '{prefix}'."
            module_logger.info(msg)
            messages.append(f"[SKIP] {msg}")
            skipped_count += 1
            continue
        
        is_target_file_type = os.path.isfile(full_path) and item_name.lower().endswith(('.pdf', '.txt', '.epub'))
        is_directory = os.path.isdir(full_path)

        if is_target_file_type or is_directory:
            if item_name in processed_files_list:
                msg = f"Skipping '{item_name}': marked as already processed."
                module_logger.info(msg)
                messages.append(f"[SKIP] {msg}")
                skipped_count += 1
                continue
            target_items.append({'name': item_name, 'path': full_path, 'is_dir': is_directory})
        else:
            messages.append(f"[INFO] Skipping '{item_name}': not a target file type or directory.")


    if not target_items:
        msg = "No matching items found to add prefix, or all eligible items already have the prefix/were skipped."
        module_logger.info(msg)
        messages.append(f"[INFO] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "skipped_count": skipped_count, "error_count": 0}

    for item_info in tqdm(target_items, desc="API Adding Prefix", unit="item", disable=True):
        old_name, old_path, is_dir_item = item_info['name'], item_info['path'], item_info['is_dir']
        
        new_name_candidate = f"{prefix}{old_name}"
        new_path_candidate = os.path.join(input_dir, new_name_candidate)
        
        final_new_name = new_name_candidate
        final_new_path = new_path_candidate
        counter = 1

        while os.path.exists(final_new_path) and final_new_path != old_path :
            if is_dir_item:
                base_name_for_conflict = new_name_candidate # Directory name
                ext_for_conflict = ""
            else: # is file
                base_name_for_conflict, ext_for_conflict = os.path.splitext(new_name_candidate)
            
            final_new_name = f"{base_name_for_conflict}_{counter}{ext_for_conflict}"
            final_new_path = os.path.join(input_dir, final_new_name)
            counter += 1
            if counter > 100:
                msg = f"Too many name conflicts for '{old_name}' when adding prefix. Original new name: '{new_name_candidate}'. Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                error_count += 1
                overall_success = False
                final_new_path = None
                break
        
        if final_new_path is None:
            continue

        try:
            os.rename(old_path, final_new_path)
            msg = f"Prefixed: '{old_name}' -> '{final_new_name}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            processed_count += 1
        except Exception as e_rename:
            msg = f"Failed to add prefix to '{old_name}': {e_rename}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += 1
            overall_success = False
            
    final_summary = f"Prefix addition complete. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}."
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
    return {"success": overall_success, "messages": messages, "processed_count": processed_count, "skipped_count": skipped_count, "error_count": error_count}


def extract_numbers_in_filenames_api(input_dir: str) -> dict:
    """
    API-adapted: Extracts numbers from filenames and renames them.
    Args:
        input_dir (str): The directory.
    Returns:
        dict: Operation results including list of processed (new) filenames.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Extracting numbers from filenames in '{input_dir}'")
    messages = []
    processed_new_filenames = [] # Store the new names of successfully processed files
    skipped_count = 0
    error_count = 0
    failed_details = [] # List of (old_filename, error_reason)
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_new_filenames": [], "skipped_count": 0, "error_count": 1, "failed_details": []}

    try:
        all_files_in_dir = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    except Exception as e:
        msg = f"Could not read directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_new_filenames": [], "skipped_count": 0, "error_count": 1, "failed_details": []}

    for old_filename in tqdm(all_files_in_dir, desc="API Extracting Numbers", unit="file", disable=True):
        src_path = os.path.join(input_dir, old_filename)
        base_without_ext, original_ext = os.path.splitext(old_filename)

        if re.fullmatch(r'^\d+$', base_without_ext):
            msg = f"Skipping purely numeric file base: '{old_filename}'"
            module_logger.info(msg)
            messages.append(f"[SKIP] {msg}")
            skipped_count += 1
            continue

        numbers_part = re.sub(r'[^0-9-]', '', base_without_ext) # Operate on base, then add ext
        numbers_part = numbers_part.lstrip('-').rstrip('-')

        if not re.search(r'\d', numbers_part): # Check if any digit remains
            msg = f"No numbers found in filename base: '{old_filename}'. Skipping."
            module_logger.info(msg) # Changed to info as it's an expected skip
            messages.append(f"[SKIP] {msg}")
            skipped_count += 1
            continue
        
        new_name_candidate = f"{numbers_part}{original_ext}"
        new_path_candidate = os.path.join(input_dir, new_name_candidate)

        final_new_name = new_name_candidate
        final_new_path = new_path_candidate
        counter = 1

        while os.path.exists(final_new_path) and final_new_path != src_path:
            base_conflict, ext_conflict = os.path.splitext(new_name_candidate)
            final_new_name = f"{base_conflict}_{counter}{ext_conflict}"
            final_new_path = os.path.join(input_dir, final_new_name)
            counter += 1
            if counter > 1000:
                msg = f"Too many name conflicts for '{old_filename}' after number extraction. Target: '{new_name_candidate}'. Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                failed_details.append((old_filename, "Conflict resolution failed"))
                error_count += 1
                overall_success = False
                final_new_path = None
                break
        
        if final_new_path is None:
            continue

        try:
            os.rename(src_path, final_new_path)
            messages.append(f"[SUCCESS] Renamed: '{old_filename}' -> '{final_new_name}'")
            processed_new_filenames.append(final_new_name)
        except Exception as e_rename:
            msg = f"Failed to rename '{old_filename}' to '{final_new_name}': {e_rename}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            failed_details.append((old_filename, str(e_rename)))
            error_count += 1
            overall_success = False

    final_summary = (f"Number extraction complete. "
                     f"Processed renames: {len(processed_new_filenames)}, Skipped: {skipped_count}, Errors: {error_count}.")
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
        
    return {
        "success": overall_success and error_count == 0, # Overall success only if no errors
        "messages": messages,
        "processed_new_filenames": processed_new_filenames, # Return new names
        "processed_count": len(processed_new_filenames),
        "skipped_count": skipped_count,
        "error_count": error_count,
        "failed_details": failed_details
    }

def reverse_rename_api(input_dir: str) -> dict:
    """
    API-adapted: Reverse renaming (removes prefix).
    Args:
        input_dir (str): The directory.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Reverse renaming in '{input_dir}'")
    messages = []
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    failed_details = []
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "renamed_count": 0, "skipped_count":0, "error_count": 1, "failed_details": []}

    try:
        items_in_dir = os.listdir(input_dir)
    except Exception as e:
        msg = f"Could not read directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "renamed_count": 0, "skipped_count":0, "error_count": 1, "failed_details": []}

    for old_name in tqdm(items_in_dir, desc="API Reverse Renaming", unit="item", disable=True):
        old_path = os.path.join(input_dir, old_name)
        
        match = re.match(r'^([A-Z\u4e00-\u9fff])-(.+)$', old_name)
        if not match:
            msg = f"Skipping '{old_name}': does not match 'X-name' format."
            # module_logger.debug(msg) # Can be debug if too verbose for info
            messages.append(f"[SKIP] {msg}")
            skipped_count += 1
            continue

        new_name_candidate = match.group(2)
        if not new_name_candidate: # e.g. original was "A-.txt"
            msg = f"Skipping '{old_name}': new name would be empty after removing prefix."
            module_logger.warning(msg)
            messages.append(f"[WARN] {msg}")
            skipped_count +=1
            continue

        new_path_candidate = os.path.join(input_dir, new_name_candidate)
        
        final_new_name = new_name_candidate
        final_new_path = new_path_candidate
        counter = 1

        while os.path.exists(final_new_path) and final_new_path != old_path:
            # Determine if it's a file or dir for proper extension handling in conflict
            is_file_item = os.path.isfile(old_path) # Check original type
            base_conflict, ext_conflict = os.path.splitext(new_name_candidate) if is_file_item else (new_name_candidate, "")

            final_new_name = f"{base_conflict}_{counter}{ext_conflict}"
            final_new_path = os.path.join(input_dir, final_new_name)
            counter += 1
            if counter > 100:
                msg = f"Too many name conflicts for '{old_name}' during reverse rename. Target: '{new_name_candidate}'. Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                failed_details.append((old_name, "Conflict resolution failed"))
                error_count += 1
                overall_success = False
                final_new_path = None
                break
        
        if final_new_path is None:
            continue

        try:
            os.rename(old_path, final_new_path)
            msg = f"Reverse renamed: '{old_name}' -> '{final_new_name}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            renamed_count += 1
        except Exception as e_rename:
            msg = f"Failed to reverse rename '{old_name}' to '{final_new_name}': {e_rename}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            failed_details.append((old_name, str(e_rename)))
            error_count += 1
            overall_success = False

    final_summary = (f"Reverse renaming complete. "
                     f"Renamed items: {renamed_count}, Skipped: {skipped_count}, Errors: {error_count}.")
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
        
    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "renamed_count": renamed_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "failed_details": failed_details
    }

def add_filename_suffix_api(input_dir: str, suffix: str, processed_files_list: list = None) -> dict:
    """
    API-adapted: Adds a suffix to filenames.
    Args:
        input_dir (str): The directory.
        suffix (str): The suffix to add.
        processed_files_list (list, optional): Files already processed to skip.
    Returns:
        dict: Operation results.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Adding suffix '{suffix}' in '{input_dir}'")
    messages = []
    processed_count = 0
    skipped_count = 0
    error_count = 0
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "skipped_count": 0, "error_count": 1}

    try:
        items_in_dir = os.listdir(input_dir)
    except Exception as e:
        msg = f"Could not read directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "processed_count": 0, "skipped_count": 0, "error_count": 1}

    if processed_files_list is None:
        processed_files_list = []

    target_items = []
    for item_name in items_in_dir:
        full_path = os.path.join(input_dir, item_name)
        base_name, ext = os.path.splitext(item_name)
        if base_name.endswith(suffix):
            msg = f"Skipping '{item_name}': already has suffix '{suffix}'."
            module_logger.info(msg)
            messages.append(f"[SKIP] {msg}")
            skipped_count += 1
            continue
        
        is_target_file_type = os.path.isfile(full_path) and item_name.lower().endswith(('.pdf', '.txt', '.epub'))
        is_directory = os.path.isdir(full_path)

        if is_target_file_type or is_directory:
            if item_name in processed_files_list:
                msg = f"Skipping '{item_name}': marked as already processed."
                module_logger.info(msg)
                messages.append(f"[SKIP] {msg}")
                skipped_count += 1
                continue
            target_items.append({'name': item_name, 'path': full_path, 'is_dir': is_directory})
        else:
            messages.append(f"[INFO] Skipping '{item_name}': not a target file type or directory.")

    if not target_items:
        msg = "No matching items found to add suffix, or all eligible items already have the suffix/were skipped."
        module_logger.info(msg)
        messages.append(f"[INFO] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "skipped_count": skipped_count, "error_count": 0}

    for item_info in tqdm(target_items, desc="API Adding Suffix", unit="item", disable=True):
        old_name, old_path, is_dir_item = item_info['name'], item_info['path'], item_info['is_dir']
        
        if is_dir_item:
            new_name_candidate = f"{old_name}{suffix}"
        else:
            base_name, ext = os.path.splitext(old_name)
            base_name = base_name.rstrip('.pdf').rstrip('.txt').rstrip('.epub')
            new_name_candidate = f"{base_name}{suffix}{ext}"
            new_name_candidate = _remove_duplicate_extension(new_name_candidate)
            
        new_path_candidate = os.path.join(input_dir, new_name_candidate)
        
        final_new_name = new_name_candidate
        final_new_path = new_path_candidate
        counter = 1

        while os.path.exists(final_new_path) and final_new_path != old_path:
            if is_dir_item:
                base_name_for_conflict = new_name_candidate
                ext_for_conflict = ""
            else:
                base_name_for_conflict, ext_for_conflict = os.path.splitext(new_name_candidate)
            
            final_new_name = f"{base_name_for_conflict}_{counter}{ext_for_conflict}"
            final_new_path = os.path.join(input_dir, final_new_name)
            counter += 1
            if counter > 100:
                msg = f"Too many name conflicts for '{old_name}' when adding suffix. Original new name: '{new_name_candidate}'. Skipping."
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                error_count += 1
                overall_success = False
                final_new_path = None
                break
        
        if final_new_path is None:
            continue

        try:
            os.rename(old_path, final_new_path)
            msg = f"Suffixed: '{old_name}' -> '{final_new_name}'"
            module_logger.info(msg)
            messages.append(f"[SUCCESS] {msg}")
            processed_count += 1
        except Exception as e_rename:
            msg = f"Failed to add suffix to '{old_name}': {e_rename}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += 1
            overall_success = False
            
    final_summary = f"Suffix addition complete. Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}."
    module_logger.info(final_summary)
    messages.append(f"[INFO] {final_summary}")
    return {"success": overall_success, "messages": messages, "processed_count": processed_count, "skipped_count": skipped_count, "error_count": error_count}

def _remove_duplicate_extension(name: str) -> str:
    """
    移除重复扩展名，如 '炼狱.txt.txt' -> '炼狱.txt'
    """
    base, ext = os.path.splitext(name)
    while base.endswith(ext) and ext:
        base = base[:-(len(ext))]
    return base + ext