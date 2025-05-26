import os
import zipfile
import py7zr
import rarfile
import tarfile
import patoolib
import shutil
import logging
import getpass
from tqdm import tqdm

logger = logging.getLogger(__name__)

SUPPORTED_ARCHIVES = ('.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.iso')
DEFAULT_PASSWORD = "1111"  # Default decompression password

def _try_extract_with_password(file_path: str, extract_dir: str) -> bool:
    """
    Attempts to extract an encrypted archive with a password (internal function).
    Args:
        file_path (str): Path to the archive file
        extract_dir (str): Destination directory for extraction
    Returns:
        bool: True if extraction was successful, False otherwise.
    Process:
        1. Prioritizes using DEFAULT_PASSWORD.
        2. Prompts the user for manual password input if the default fails.
        3. Attempts password up to 3 times.
    """
    retry_count = 0
    while retry_count < 3:
        try:
            password = DEFAULT_PASSWORD if retry_count == 0 else getpass.getpass(f"Please enter the password for {os.path.basename(file_path)}: ")

            if file_path.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path, metadata_encoding='gb18030') as zf:
                    zf.extractall(extract_dir, pwd=password.encode('gb18030'))
            elif file_path.lower().endswith('.7z'):
                with py7zr.SevenZipFile(file_path, password=password) as zf:
                    zf.extractall(extract_dir)
            elif file_path.lower().endswith('.rar'):
                with rarfile.RarFile(file_path, charset='gbk') as rf:
                    rf.extractall(extract_dir, pwd=password)
            else: # For other formats like tar.gz, tar.bz2, etc. handled by patoolib
                patoolib.extract_archive(
                    file_path,
                    outdir=extract_dir,
                    password=password,
                    verbosity=-1  # Disable patoolib output
                )
            return True
        except Exception as e:
            logger.error(f"Password attempt failed ({retry_count+1}/3) for {os.path.basename(file_path)}: {e}")
            retry_count += 1
    return False

def extract_archives(input_dir: str) -> None:
    """
    Extracts all supported archive files in the specified input directory.
    Supported formats: zip/7z/rar/tar/gz/bz2/xz/iso
    Processing logic:
        1. Automatically detects encrypted archives.
        2. Prioritizes trying the default password "1111".
        3. Supports Chinese encoding (GB18030/GBK).
        4. Deletes the original archive after successful extraction.
    Error handling:
        - Allows manual password input for incorrect passwords (up to 3 attempts).
        - Automatically cleans up temporary directories upon extraction failure.

    Args:
        input_dir (str): The directory containing the archive files to extract.
    """
    logger.info(f"Starting archive extraction in: {input_dir}")
    archive_files = [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_ARCHIVES)]

    if not archive_files:
        logger.info(f"No supported archive files found in '{input_dir}'.")
        return

    for archive in tqdm(archive_files, desc="Extracting files"):
        file_path = os.path.join(input_dir, archive)
        extract_dir = os.path.join(input_dir, os.path.splitext(archive)[0])
        success = False

        try:
            os.makedirs(extract_dir, exist_ok=True)

            # Prioritize trying extraction without password
            try:
                if archive.lower().endswith('.zip'):
                    with zipfile.ZipFile(file_path, metadata_encoding='gb18030') as zf:
                        zf.extractall(extract_dir)
                elif archive.lower().endswith('.7z'):
                    with py7zr.SevenZipFile(file_path) as zf:
                        zf.extractall(extract_dir)
                elif archive.lower().endswith('.rar'):
                    with rarfile.RarFile(file_path, charset='gbk') as rf:
                        rf.extractall(extract_dir)
                elif archive.lower().endswith(('.tar', '.gz', '.bz2', '.xz')):
                    with tarfile.open(file_path, encoding='gb18030') as tf:
                        tf.extractall(extract_dir)
                else: # Fallback for other types supported by patoolib, like .iso if patoolib is configured
                    patoolib.extract_archive(file_path, outdir=extract_dir)
                success = True
            except (RuntimeError, patoolib.util.PatoolError, rarfile.PasswordRequired) as e:
                # If extraction fails due to password or other runtime errors, try with password
                if "password" in str(e).lower() or isinstance(e, rarfile.PasswordRequired):
                    logger.info(f"Encrypted file detected or password required: {archive}. Attempting password...")
                    success = _try_extract_with_password(file_path, extract_dir)
                else:
                    raise # Re-raise other unexpected errors

            if success:
                logger.info(f"Successfully extracted: {archive} -> {extract_dir}")
                # Delete original archive after successful extraction
                os.remove(file_path)
            else:
                logger.warning(f"Extraction failed for: {archive}")
                # Clean up partially extracted directory if extraction failed
                if os.path.exists(extract_dir) and os.path.isdir(extract_dir) and not os.listdir(extract_dir):
                    # Only remove if directory is empty (or was just created for failed extraction)
                    try:
                        shutil.rmtree(extract_dir)
                        logger.info(f"Cleaned up empty extraction directory: {extract_dir}")
                    except Exception as clean_e:
                        logger.warning(f"Failed to clean up empty directory {extract_dir}: {clean_e}")
                elif os.path.exists(extract_dir) and os.path.isdir(extract_dir):
                    logger.warning(f"Extraction directory '{extract_dir}' not empty, not removing.")

        except Exception as e:
            logger.error(f"Error during extraction of {archive}: {type(e).__name__} - {e}")
            # Ensure cleanup if an unhandled error occurred during the overall process
            if os.path.exists(extract_dir) and os.path.isdir(extract_dir) and not os.listdir(extract_dir):
                try:
                    shutil.rmtree(extract_dir)
                    logger.info(f"Cleaned up empty extraction directory due to error: {extract_dir}")
                except Exception as clean_e:
                    logger.warning(f"Failed to clean up empty directory {extract_dir} after error: {clean_e}")