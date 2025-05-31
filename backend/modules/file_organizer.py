# backend/modules/file_organizer.py
import os
import shutil
import unicodedata
import re
import logging
from tqdm import tqdm
from collections import defaultdict


module_logger = logging.getLogger(__name__)

def normalize_str(s: str) -> str:
    """
    Normalizes a string using NFC (Normalization Form Canonical Composition).
    """
    return unicodedata.normalize('NFC', s)

def clean_name_for_grouping(filename: str) -> str:
    """
    Cleans a filename specifically for grouping logic.
    Removes bracketed author names, extensions, and truncates at specific symbols or numbers.
    """
    # Remove author name (content in []) and extension
    cleaned = filename
    if cleaned.startswith('['):
        try:
            idx = cleaned.index(']') + 1
            cleaned = cleaned[idx:].strip()
        except ValueError:
            pass # No closing bracket found
    cleaned = os.path.splitext(cleaned)[0] # Remove extension
    cleaned = normalize_str(cleaned)

    # Truncate at the first occurrence of numbers or specific symbols
    # This helps in finding more relevant common substrings for titles.
    cut_pos = len(cleaned)
    for ch in '0123456789[]()@#%&': # Added more symbols that might denote end of a title
        pos = cleaned.find(ch)
        if pos != -1 and pos < cut_pos:
            cut_pos = pos
    cleaned = cleaned[:cut_pos].strip()
    
    cleaned = re.sub(r'\s+', ' ', cleaned) # Compress multiple spaces
    return cleaned

def _longest_common_substring_optimized(s1: str, s2: str, min_length: int = 5) -> str:
    """
    Optimized to find the longest common substring.
    Returns the common substring if its length is `min_length` or more.
    """
    # Ensure s1 is the shorter string for minor optimization
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    
    m = len(s1)
    n = len(s2)
    longest = 0
    ending_index_s1 = m

    for i in range(m):
        for j in range(n):
            current_match_length = 0
            # Check how many characters match starting from s1[i] and s2[j]
            while (i + current_match_length < m and
                   j + current_match_length < n and
                   s1[i + current_match_length] == s2[j + current_match_length]):
                current_match_length += 1
            
            if current_match_length > longest:
                longest = current_match_length
                ending_index_s1 = i + current_match_length
            # Optimization: if remaining part of s1 is shorter than current longest, no need to check further
            if m - (i + 1) < longest:
                break 
                
    if longest >= min_length:
        return s1[ending_index_s1 - longest : ending_index_s1]
    return ""


def _group_files_by_common_substring_optimized(filenames: list[str], min_common_len: int = 5) -> list[list[str]]:
    """
    Groups files based on the longest common substring in their cleaned names.
    This version tries to be more robust in grouping.
    """
    if not filenames:
        return []

    cleaned_names_map = {fname: clean_name_for_grouping(fname) for fname in filenames}
    
    # Sort filenames to ensure deterministic behavior, e.g., by cleaned name then original name
    sorted_filenames = sorted(filenames, key=lambda f: (cleaned_names_map[f], f))

    groups = []
    processed_files = set()

    for i in range(len(sorted_filenames)):
        file1 = sorted_filenames[i]
        if file1 in processed_files:
            continue

        current_group = [file1]
        processed_files.add(file1)
        base1 = cleaned_names_map[file1]

        if not base1: # Skip if cleaned name is empty
            groups.append(current_group) # Single file group
            continue

        # Find other files that share a significant common substring with file1
        for j in range(i + 1, len(sorted_filenames)):
            file2 = sorted_filenames[j]
            if file2 in processed_files:
                continue
            
            base2 = cleaned_names_map[file2]
            if not base2:
                continue

            common_sub = _longest_common_substring_optimized(base1, base2, min_length=min_common_len)
            
            # Heuristic: common substring should be a significant part of at least one name
            # and not just a very short common word.
            # Also, ensure the common substring is not too generic (e.g. "the", "a") by length.
            if common_sub and (len(common_sub) > 0.3 * len(base1) or len(common_sub) > 0.3 * len(base2)):
                current_group.append(file2)
                processed_files.add(file2)
        
        groups.append(current_group)

    # Handle remaining ungrouped files as single-file groups
    for fname in sorted_filenames:
        if fname not in processed_files:
            groups.append([fname])
            processed_files.add(fname)
            
    return groups


def _get_folder_name_for_group_optimized(group: list[str], min_common_len_for_foldername: int = 4) -> str:
    """
    Determines a folder name for a group.
    Tries to find a common prefix or a significant common substring.
    Falls back to the cleaned name of the first file if no good commonality is found.
    """
    if not group:
        return "Unnamed_Group"
    
    cleaned_group_names = [clean_name_for_grouping(f) for f in group]
    # Filter out empty cleaned names which can happen if filename is only symbols/numbers
    cleaned_group_names = [name for name in cleaned_group_names if name] 

    if not cleaned_group_names: # All names resulted in empty cleaned names
        # Fallback to a generic name based on the first original filename
        return re.sub(r'[\\/*?:"<>|]', '_', os.path.splitext(group[0])[0])[:50] or "Organized_Files"


    if len(cleaned_group_names) == 1:
        # For a single file group, use its cleaned name for the folder.
        # Ensure it's not empty after cleaning.
        folder_name = cleaned_group_names[0][:50].strip()
        if not folder_name: # If cleaned name became empty (e.g. "123.pdf" cleaned to "")
             # Fallback to original filename without extension, sanitized
            folder_name = re.sub(r'[\\/*?:"<>|]', '_', os.path.splitext(group[0])[0])[:50].strip()
        return folder_name or "Organized_File" # Final fallback for single file

    # Try common prefix first for groups with multiple files
    common_prefix = os.path.commonprefix(cleaned_group_names)
    if len(common_prefix) >= min_common_len_for_foldername and common_prefix.strip():
        # Further clean the prefix: remove trailing common words or hyphens
        common_prefix = common_prefix.strip(' -_')
        if len(common_prefix) >= min_common_len_for_foldername:
             return common_prefix[:50] # Truncate

    # If no good common prefix, try longest common substring among all in the group
    if len(cleaned_group_names) > 1:
        current_lcs = cleaned_group_names[0]
        for i in range(1, len(cleaned_group_names)):
            current_lcs = _longest_common_substring_optimized(current_lcs, cleaned_group_names[i], min_length=min_common_len_for_foldername)
            if not current_lcs: # If at any point LCS becomes empty, fallback
                break
        if current_lcs and len(current_lcs.strip(' -_')) >= min_common_len_for_foldername:
            return current_lcs.strip(' -_')[:50]

    # Fallback to the cleaned name of the first file in the group if other methods fail
    # Ensure it's not empty after cleaning.
    fallback_folder_name = cleaned_group_names[0][:50].strip()
    if not fallback_folder_name:
        fallback_folder_name = re.sub(r'[\\/*?:"<>|]', '_', os.path.splitext(group[0])[0])[:50].strip()
    return fallback_folder_name or "Organized_Group"


def organize_files_by_group_api(input_dir: str, 
                                target_extensions_str: str = ".pdf .epub .txt .jpg .jpeg .png .gif .bmp .tiff .webp .zip .rar .7z .tar .gz"
                                ) -> dict:
    """
    API-adapted: Organizes files into groups based on common substrings in their names.
    Args:
        input_dir (str): Directory containing files to organize.
        target_extensions_str (str): Space-separated list of file extensions to process.
    Returns:
        dict: Operation results including moved files details and error information.
    """
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"API: Organizing files by group in '{input_dir}'")
    messages = []
    moved_files_details = []  # Track successful moves
    skipped_files_details = []  # Track skipped files
    error_details = []  # Track errors
    moved_count = 0
    skipped_count = 0
    error_count = 0
    overall_success = True

    # Input validation and setup
    target_extensions = set(ext.lower() for ext in target_extensions_str.split())
    
    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        all_target_files = [
            f for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f)) and 
               os.path.splitext(f)[1].lower() in target_extensions
        ]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not all_target_files:
        msg = f"No files with specified target extensions found in '{input_dir}'."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "moved_count": 0, "skipped_count":0, "error_count": 0}

    # Group files by common substrings for intelligent organization
    file_groups = _group_files_by_common_substring_optimized(all_target_files, min_common_len=5)
    
    total_files_to_process = len(all_target_files)

    for group in tqdm(file_groups, desc="API Organizing Files", unit="group", disable=True):
        if not group: continue

        folder_name_raw = _get_folder_name_for_group_optimized(group, min_common_len_for_foldername=3) # min_common_len for folder name can be shorter
        
        folder_name_sanitized = re.sub(r'[\\/*?:"<>|]', '_', folder_name_raw).strip()
        if not folder_name_sanitized: 
            # Fallback if sanitized name is empty, use first part of the first file name
            base_name = os.path.splitext(group[0])[0]
            folder_name_sanitized = re.sub(r'[\\/*?:"<>|]', '_', base_name[:20]).strip() or f"Group_{group[0][:10]}"
        
        if not folder_name_sanitized : # Absolute fallback
             folder_name_sanitized = "Misc_Group"


        folder_path = os.path.join(input_dir, folder_name_sanitized)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            # messages.append(f"[INFO] Ensured directory: '{folder_name_sanitized}'") # Can be too verbose
        except Exception as e_mkdir:
            msg = f"Could not create directory '{folder_name_sanitized}': {e_mkdir}. Skipping group."
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_count += len(group) 
            for fname_err in group:
                error_details.append({"file": fname_err, "error": f"Failed to create group folder '{folder_name_sanitized}'"})
            overall_success = False
            continue

        for original_filename in group:
            source_path = os.path.join(input_dir, original_filename)
            destination_path = os.path.join(folder_path, original_filename)

            if not os.path.exists(source_path): 
                msg = f"Source file '{original_filename}' no longer exists in root. Possibly already moved or handled."
                module_logger.warning(msg)
                # messages.append(f"[WARN] {msg}") # Can be too verbose
                # Do not count as skipped if it was meant to be in this group but already moved by another logic path (e.g. if file was in multiple "potential" groups based on LCS)
                # The processed_files set in _group_files_by_common_substring_optimized should handle this.
                # This check is a safeguard.
                continue 
            
            if os.path.abspath(source_path) == os.path.abspath(destination_path): # Trying to move to itself (already in a folder of its own name)
                 skipped_files_details.append({"file": original_filename, "reason": "File is already in its correct target folder."})
                 skipped_count +=1
                 continue

            if os.path.exists(destination_path):
                # Handle conflict: append a number to the filename in the destination
                base, ext = os.path.splitext(original_filename)
                counter = 1
                new_destination_path = destination_path
                while os.path.exists(new_destination_path):
                    new_filename = f"{base}_{counter}{ext}"
                    new_destination_path = os.path.join(folder_path, new_filename)
                    counter += 1
                    if counter > 100: # Safety break for too many conflicts
                        msg = f"Too many conflicts for '{original_filename}' in folder '{folder_name_sanitized}'. Skipping."
                        module_logger.error(msg)
                        messages.append(f"[ERROR] {msg}")
                        error_details.append({"file": original_filename, "error": "Too many name conflicts in destination folder"})
                        error_count +=1
                        overall_success = False
                        new_destination_path = None # Mark as failed
                        break
                if new_destination_path is None:
                    continue
                destination_path = new_destination_path


            try:
                shutil.move(source_path, destination_path)
                final_moved_filename = os.path.basename(destination_path)
                messages.append(f"[SUCCESS] Moved '{original_filename}' to '{folder_name_sanitized}/{final_moved_filename}'.")
                moved_files_details.append({"file": original_filename, "moved_to_file": final_moved_filename, "destination_folder": folder_name_sanitized})
                moved_count += 1
            except Exception as e_move:
                msg = f"Failed to move '{original_filename}' to '{folder_name_sanitized}': {e_move}"
                module_logger.error(msg)
                messages.append(f"[ERROR] {msg}")
                error_details.append({"file": original_filename, "error": msg})
                error_count += 1
                overall_success = False
    
    final_summary_msg = (f"File organization finished. Total target files found: {total_files_to_process}. "
                         f"Moved: {moved_count}, Skipped: {skipped_count}, Errors: {error_count}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_target_files_found": total_files_to_process,
        "files_moved": moved_count,
        "files_skipped": skipped_count,
        "errors_occurred": error_count,
        "moved_files_details": moved_files_details,
        "skipped_files_details": skipped_files_details,
        "error_details": error_details
    }