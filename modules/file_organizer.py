import os
import shutil
import unicodedata
import re
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)
# Configure logging if this module is run standalone, otherwise it will use parent's config
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

def longest_common_substring(s1: str, s2: str) -> str:
    """
    Finds the longest common substring between two strings.
    Returns the common substring if its length is 5 or more, otherwise an empty string.
    Args:
        s1 (str): First string.
        s2 (str): Second string.
    Returns:
        str: The longest common substring or an empty string.
    """
    m, n = len(s1), len(s2)
    max_len = 0
    end_index = 0
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    end_index = i
            else:
                dp[i][j] = 0
    if max_len >= 5:
        return s1[end_index - max_len:end_index]
    else:
        return ""

def group_files_by_common_substring(filenames: list[str]) -> list[list[str]]:
    """
    Groups files by their longest common substring in their cleaned names.
    Args:
        filenames (list[str]): A list of filenames to group.
    Returns:
        list[list[str]]: A list of groups, where each group is a list of filenames.
    """
    groups = []
    assigned = set()

    for i, f1 in enumerate(filenames):
        if f1 in assigned:
            continue
        base1 = clean_name(f1)
        group = [f1]
        assigned.add(f1)
        for j in range(i + 1, len(filenames)):
            f2 = filenames[j]
            if f2 in assigned:
                continue
            base2 = clean_name(f2)
            common = longest_common_substring(base1, base2)
            if common:
                group.append(f2)
                assigned.add(f2)
        groups.append(group)
    return groups

def get_folder_name_for_group(group: list[str]) -> str:
    """
    Determines a suitable folder name for a group of files.
    If a single file, uses its cleaned name. If multiple, finds the longest common substring.
    Args:
        group (list[str]): A list of filenames in a group.
    Returns:
        str: The suggested folder name.
    """
    bases = [clean_name(f) for f in group]
    if len(group) == 1:
        return bases[0]
    else:
        longest = ""
        for i in range(len(bases)):
            for j in range(i + 1, len(bases)):
                common = longest_common_substring(bases[i], bases[j])
                if len(common) > len(longest):
                    longest = common
        return longest if longest else bases[0]

def organize_files_by_group(input_dir: str, target_extensions: set[str]) -> None:
    """
    Organizes files in the specified input directory into subfolders based on
    common substrings in their filenames.
    Args:
        input_dir (str): The directory containing files to organize.
        target_extensions (set[str]): A set of file extensions to consider for organization.
    """
    logger.info(f"Starting file organization in: {input_dir}")
    logger.info(f"Target extensions: {target_extensions}")

    all_files = [f for f in os.listdir(input_dir)
                 if os.path.isfile(os.path.join(input_dir, f)) and
                 os.path.splitext(f)[1].lower() in target_extensions]

    if not all_files:
        logger.info(f"No files with target extensions found in '{input_dir}'. Skipping organization.")
        return

    groups = group_files_by_common_substring(all_files)
    moved_count = 0

    for group in tqdm(groups, desc="Organizing Files"):
        folder_name = get_folder_name_for_group(group)
        if not folder_name: # Fallback if no suitable folder name can be generated
            logger.warning(f"Could not determine a suitable folder name for group: {group}. Skipping this group.")
            continue

        folder_path = os.path.join(input_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Created/Ensured directory: {folder_path}")

        for fname in group:
            src = os.path.join(input_dir, fname)
            dst = os.path.join(folder_path, fname)
            
            if not os.path.exists(src): # Check if source file still exists (might have been moved by another group)
                logger.warning(f"Source file no longer exists, skipping: {src}")
                continue

            if os.path.exists(dst):
                logger.warning(f"File already exists in target folder, skipping move: {dst}")
                continue
            
            try:
                shutil.move(src, dst)
                logger.info(f"Moved file '{fname}' to folder '{folder_name}'")
                moved_count += 1
            except Exception as e:
                logger.error(f"Failed to move file '{fname}' to '{folder_name}': {e}")
    
    logger.info(f"File organization complete. Moved {moved_count} files.")