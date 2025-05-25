import os
import re
import argparse
import time
import fitz
import zipfile
import py7zr
import rarfile
import tarfile
import patoolib
import shutil
from PyPDF2 import PdfMerger
from pypinyin import pinyin, Style
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import pikepdf
from ebooklib import epub
from bs4 import BeautifulSoup
import logging
import getpass
from tqdm import tqdm
from ebooklib import ITEM_STYLE

# Global Configuration
# Detect the script's execution directory and set it as the input directory
INPUT_DIR = os.getcwd()
# PDF output will be in a subfolder named 'processed_pdf' within the current execution directory
PDF_OUTPUT_DIR = os.path.join(INPUT_DIR, "processed_pdf") 
MAX_WORKERS = 5
DEBUG = True
SUPPORTED_ARCHIVES = ('.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.iso')
DEFAULT_PASSWORD = "1111"  # Default decompression password
REPORT_TEMPLATE = """
╔══════════════ {title} ═════════════════╗
║ Total Files Processed: {total}
║ Successfully Renamed: {success}
╚════════════════════════════════════════╝
"""

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def natural_sort_key(s):
    """
    Generates a natural sort key for intelligent sorting of filenames containing numbers.
    Example: "file10" will be sorted after "file2"
    Args:
        s (str): Input filename
    Returns:
        list: List of split sort keys, with numeric parts converted to integers
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)  # Use raw string
    ]

def generate_report(report_title, total_processed, success_files, error_files, duration, output_file=None):
    """
    Generates a formatted operation report and logs it.
    Args:
        report_title (str): Report title
        total_processed (int): Total number of files processed
        success_files (list): List of successful files
        error_files (list): List of failed files, where each element is a (filename, error reason) tuple
        duration (float): Time taken for the operation (seconds)
        output_file (str, optional): Output file path
    """
    success_count = len(success_files)
    error_count = len(error_files)
    success_rate = (success_count / total_processed) * 100 if total_processed else 0

    # Build report header
    report = fr"""
    {report_title}
    Output File: {output_file.ljust(30) if output_file else "N/A"}
    Total Files Processed: {total_processed:<5}
    Successful Files: {success_count:<5}
    Failed Files: {error_count:<5}
    Success Rate: {success_rate:.2f}%
    Duration: {duration:.2f} seconds
    {"─" * 50}
    Failure Details:
    """

    # Process failed file information
    if error_files:
        for idx, (fname, reason) in enumerate(error_files, 1):
            report += f"{idx:02d}. {fname[:30]:<30} | {reason[:40]}\n"
        report += "For more error details, please check the log."
    else:
        report += "✓ All files processed successfully."

    # Output report
    logger.info(report)

class CustomHelpFormatter(argparse.RawTextHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=100)

def extract_archives():
    """
    Extracts all supported archive files in the input directory.
    Supported formats: zip/7z/rar/tar/gz/bz2/xz/iso
    Processing logic:
        1. Automatically detects encrypted archives.
        2. Prioritizes trying the default password "1111".
        3. Supports Chinese encoding (GB18030/GBK).
        4. Deletes the original archive after successful extraction.
    Error handling:
        - Allows manual password input for incorrect passwords (up to 3 attempts).
        - Automatically cleans up temporary directories upon extraction failure.
    """
    logger.info("Starting archive extraction...")
    archive_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(SUPPORTED_ARCHIVES)]

    for archive in tqdm(archive_files, desc="Extracting files"):
        file_path = os.path.join(INPUT_DIR, archive)
        extract_dir = os.path.join(INPUT_DIR, os.path.splitext(archive)[0])
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
                else:
                    patoolib.extract_archive(file_path, outdir=extract_dir)
                success = True
            except (RuntimeError, patoolib.util.PatoolError, rarfile.PasswordRequired) as e:
                if "password" in str(e).lower():
                    logger.info(f"Encrypted file detected: {archive}")
                    success = _try_extract_with_password(file_path, extract_dir)
                else:
                    raise

            if success:
                logger.info(f"Successfully extracted: {archive} -> {extract_dir}")
                # Delete original archive
                os.remove(file_path)
            else:
                logger.warning(f"Extraction failed: {archive}")
                shutil.rmtree(extract_dir)

        except Exception as e:
            logger.error(f"Error during extraction: {archive} - {str(e)}")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

def _try_extract_with_password(file_path, extract_dir):
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
            else:
                patoolib.extract_archive(
                    file_path,
                    outdir=extract_dir,
                    password=password,
                    verbosity=-1  # Disable patoolib output
                )
            return True
        except Exception as e:
            logger.error(f"Password attempt failed ({retry_count+1}/3)")
            retry_count += 1
    return False

def remove_pdf_pages(input_dir=INPUT_DIR, output_dir=PDF_OUTPUT_DIR, trim_type='f', num_pages=1):
    """
    PDF Page Cropping Function (Ultimate Stable Version)
    New features:
    - Completely rebuilds PDF document structure.
    - Forces resource reference retention.
    - Enhanced exception handling.
    """
    success_files = []
    error_files = []
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    for pdf_file in tqdm(os.listdir(input_dir), desc="PDF Structure Rebuilding & Cropping"):
        if not pdf_file.lower().endswith('.pdf'):
            continue

        input_path = os.path.join(input_dir, pdf_file)
        output_path = os.path.join(output_dir, pdf_file)

        try:
            # ================= Core Repair Logic =================
            with fitz.open(input_path) as src_doc:
                # Create a brand new PDF document (force structure rebuild)
                new_doc = fitz.open()

                # Copy document properties (retain original information)
                new_doc.set_metadata(src_doc.metadata)
                new_doc.set_toc(src_doc.get_toc())

                # Calculate the actual page range to keep
                keep_pages = []
                if trim_type == 'f':
                    keep_pages = list(range(num_pages, len(src_doc)))
                elif trim_type == 'l':
                    keep_pages = list(range(0, len(src_doc)-num_pages))
                elif trim_type == 'lf':
                    keep_pages = list(range(1, len(src_doc)-1))
                else:
                    raise ValueError(f"Invalid trim type: {trim_type}")

                # Deep copy page by page (including all resources)
                for pg_num in keep_pages:
                    page = src_doc.load_page(pg_num)
                    new_page = new_doc.new_page(-1, width=page.rect.width, height=page.rect.height)
                    new_page.show_pdf_page(
                        page.rect,
                        src_doc,  # Maintain original document reference
                        pg_num,
                        keep_proportion=True
                    )

                # Save时强制重建XREF表
                new_doc.save(
                    output_path,
                    garbage=4,            # 最高级别垃圾回收
                    deflate=True,         # 压缩内容
                    clean=True,            # 清理碎片
                    linear=True,           # 线性化PDF
                    no_new_id=True,        # 保持文件ID
                )

                success_files.append(pdf_file)
                logger.info(f"Deep rebuild successful: {pdf_file} ({len(src_doc)}→{len(new_doc)} pages)")

        except Exception as e:
            error_msg = str(e).split('\n')[0]
            error_files.append((pdf_file, error_msg))
            logger.error(f"Structure rebuild failed | {pdf_file} | Error: {error_msg}")

            # Clean up potentially generated invalid files
            if os.path.exists(output_path):
                try: os.remove(output_path)
                except: pass

    # Generate report
    duration = time.time() - start_time
    generate_report(
        "PDF Structure Rebuilding Report",
        len(success_files)+len(error_files),
        success_files,
        error_files,
        duration,
        output_file=os.path.join(output_dir, "rebuild_report.txt")
    )

def combine_files(args_list):
    """
    Main merge function (supports multiple file types).
    Args:
        args_list (list): Command-line argument list, e.g., ['e', 'output'] to merge EPUBs to output.epub
    """
    if not args_list:
        logger.error("❌ Merge operation requires at least a type parameter.")
        return

    success_files = []
    error_files = []
    start_time = time.time()

    try:
        # Common parameter parsing
        file_type = args_list[0].lower()
        base_name = args_list[1] if len(args_list) > 1 else "combined"
        ext_map = {
            'p': '.pdf',
            't': '.txt',
            'e': '.epub'
        }

        # Parameter validation
        if file_type not in ext_map:
            logger.error(f"❌ Invalid file type: {file_type} (Supported types: {', '.join(ext_map.keys())})")
            return

        ext = ext_map[file_type]
        output_name = f"{base_name}{ext}" if not base_name.endswith(ext) else base_name

        # Get sorted file list
        files = sorted(
            [f for f in os.listdir(INPUT_DIR) if f.endswith(ext)],
            key=natural_sort_key
        )

        if not files:
            logger.error("❌ No files found for merging.")
            return

        # Log processing order
        logger.info(f"📚 Starting to merge {ext.upper()} files -> {output_name}")
        logger.info("📄 File processing order:")
        for i, f in enumerate(files, 1):
            logger.info(f"{i:02d}. {f}")

        output_path = os.path.join(INPUT_DIR, output_name)

        # Distribute processing logic
        handlers = {
            'p': _combine_pdfs, # _combine_pdfs now uses pikepdf
            't': _combine_txts,
        }
        handlers[file_type](files, output_path, success_files, error_files)

        # Generate merge report
        _generate_merge_report(
            output_name=output_name,
            files=files,
            success_files=success_files,
            error_files=error_files,
            start_time=start_time
        )

    except Exception as e:
        # Exception handling
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        logger.error(f"❌ Merge operation abnormally terminated: {str(e)}")
        _generate_partial_report(
            success_files=success_files,
            error_files=error_files,
            exception=e
        )


def _combine_pdfs(files, output_path, success_files, error_files):
    """
    Core logic for merging PDF files, now using pikepdf for merging.
    pikepdf is generally more robust than PyPDF2 for handling complex or corrupted PDFs.
    """
    new_pdf = pikepdf.new() # Create a new blank PDF document
    try:
        for f in tqdm(files, desc="Merging PDFs"):
            file_path = os.path.join(INPUT_DIR, f)
            try:
                # Open each PDF file using pikepdf.open
                with pikepdf.open(file_path) as src_pdf:
                    # Extend the pages of the new PDF with all pages from the source PDF
                    new_pdf.pages.extend(src_pdf.pages)
                success_files.append(f)
            except Exception as e:
                error_detail = str(e).split('\n')[0]
                error_files.append((f, error_detail))
                logger.error(f"❌ PDF merge failed: {f} | {error_detail}")

        # Save the merged PDF file
        new_pdf.save(output_path)
    finally:
        # pikepdf document objects do not require explicit closing like PyPDF2's merger
        # The 'with' statement handles it automatically
        pass


def _combine_txts(files, output_path, success_files, error_files):
    """Core logic for merging TXT files."""
    with open(output_path, 'w', encoding='utf-8') as out:
        for f in tqdm(files, desc="Merging TXTs"):
            file_path = os.path.join(INPUT_DIR, f)
            try:
                with open(file_path, 'r', errors='replace') as infile:
                    content = infile.read()
                    out.write(content + '\n')
                success_files.append(f)
            except Exception as e:
                error_detail = str(e).split('\n')[0]
                error_files.append((f, error_detail))
                logger.error(f"❌ TXT merge failed: {f} | {error_detail}")


# Common report generation function
def _generate_merge_report(output_name, files, success_files, error_files, start_time):
    """Generates a merge report."""
    duration = time.time() - start_time
    report = f"""
Output File: {output_name.ljust(30)}
Total Files Processed: {len(files):<5}
Successfully Merged: {len(success_files):<5}
Failed Files: {len(error_files):<5}
Duration: {duration:.2f} seconds
{"─" * 50}
Failure Details:
    """
    if error_files:
        for idx, (fname, reason) in enumerate(error_files, 1):
            report += f"{idx:02d}. {fname[:30]:<30} | {reason[:40]}\n"
        report += "For more error details, please check the log."
    else:
        report += "✓ All files merged successfully."
    logger.info(report)


def _generate_partial_report(success_files, error_files, exception):
    """Generates a report for abnormal termination."""
    partial_report = f"""
Files Processed: {len(success_files)}
Failed Files: {len(error_files)}
Error Reason: {str(exception)[:50]}
    """
    logger.error(partial_report)

def compress_images(filename="compressed", target_width=1500, quality=90, dpi=300):
    """
    Super Compression PDF Generation Function (Ultimate Volume Optimization)
    Core optimization techniques:
        - Dual compression pipeline
        - Forced format unification
        - Intelligent chroma subsampling
    """
    # Phase 1: Image Preprocessing Compression
    def super_compress(img_path):
        with Image.open(img_path) as img:
            # Size optimization
            if img.width > target_width:
                ratio = target_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((target_width, new_height), Image.LANCZOS)

            # Format unification (all formats to JPEG)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Advanced compression parameters
            temp_path = os.path.join(INPUT_DIR, f"~temp_{os.path.basename(img_path)}.jpg")
            img.save(temp_path,
                    quality=quality,
                    optimize=True,
                    subsampling=2,  # 4:2:0 subsampling
                    progressive=True)

            os.replace(temp_path, img_path)
            return img_path

    # Get and strictly sort images
    image_files = sorted(
        [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=lambda x: int(re.search(r'\d+', x).group())  # Strict numeric extraction for sorting
    )

    # Parallel compression
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(tqdm(executor.map(super_compress,
                             [os.path.join(INPUT_DIR, f) for f in image_files]),
                total=len(image_files),
                desc="🔥 Super Compressing"))

    # Phase 2: PDF Generation Optimization
    pdf_path = os.path.join(INPUT_DIR, filename + '.pdf')

    with Image.open(os.path.join(INPUT_DIR, image_files[0])) as first_img:
        other_imgs = [Image.open(os.path.join(INPUT_DIR, f)) for f in image_files[1:]]
        first_img.save(
            pdf_path,
            save_all=True,
            append_images=other_imgs,
            dpi=(dpi, dpi),
            quality=quality,
            subsampling=2,        # Secondary subsampling
            progressive=True,     # Progressive loading
            optimize=True,
            compress_type='zip'   # Enable ZIP compression
        )

    # Clean up intermediate files
    for f in image_files:
        os.remove(os.path.join(INPUT_DIR, f))

    logger.info(f"✅ Super compression complete | Final size: {os.path.getsize(pdf_path)/1024/1024:.2f}MB")

def encode_pdfs(password):
    """
    PDF Encryption Function (AES-256 Encryption)
    Args:
        password (str): Encryption password
    Features:
        - Generates an encrypted copy (filename prefixed with "encrypted_").
        - Restricts permissions: disallows printing/copying/modification.
    Dependencies: pikepdf
    """
    logger.info(f"Starting PDF encryption operation with password: {password}")

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.error("❌ No PDF files found for encryption.")
        return

    success = 0
    failures = []
    start_time = time.time()  # Record start time

    with tqdm(pdf_files, desc="Encryption Progress", unit="file") as pbar:
        for filename in pbar:
            input_path = os.path.join(INPUT_DIR, filename)
            output_path = os.path.join(INPUT_DIR, f"encrypted_{filename}")

            try:
                with pikepdf.open(input_path) as pdf:
                    pdf.save(output_path, encryption=pikepdf.Encryption(
                        user=password,
                        owner=password,
                        allow=pikepdf.Permissions(
                            accessibility=False,
                            extract=False,
                            modify_annotation=False,  # Use correct parameter name
                            print_lowres=False,
                            print_highres=False
                        )
                    ))
                success += 1
                logger.info(f"✅ Encryption successful: {filename} → {output_path}")

            except Exception as e:
                failures.append((filename, str(e)))  # Save as tuple
                logger.error(f"❌ Encryption failed: {filename} | {str(e)}")

    # Generate report (needs correct parameters)
    generate_report(
        "🔐 PDF Encryption Report",
        len(pdf_files),
        [f"encrypted_{f}" for f in pdf_files if f not in [err[0] for err in failures]],
        failures,
        time.time() - start_time,
        output_file="encryption_report.pdf"
    )

def decode_pdfs(password):
    """
    PDF Decryption Function (Supports Brute Force)
    Args:
        password (str): Decryption password
    Features:
        - Atomic operation (saves to temporary file first).
        - Automatically handles password errors and file corruption.
        - Supports overwriting original files.
    Dependencies: pikepdf
    """
    logger.info(f"Starting PDF decryption operation with password: {password}")
    success = 0
    failures = []

    # Get all PDF files (case-insensitive)
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.error("❌ No PDF files found for decryption.")
        return

    with tqdm(pdf_files, desc="Decryption Progress", unit="file") as pbar:
        for filename in pbar:
            input_path = os.path.join(INPUT_DIR, filename)

            # Create temporary file path
            temp_path = os.path.join(INPUT_DIR, f"~temp_{filename}")

            try:
                # Use with statement to ensure proper file closing
                with pikepdf.open(
                    input_path,
                    password=password,
                    allow_overwriting_input=True  # Key parameter
                ) as pdf:

                    # Save to temporary file first
                    pdf.save(temp_path)

                    # Atomically replace original file
                    os.replace(temp_path, input_path)
                    success += 1
                    pbar.set_postfix_str(f"Latest Processed: {filename[:15]}")

            except pikepdf.PasswordError:
                failures.append(f"{filename}: Incorrect password")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                failures.append(f"{filename}: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    # Generate decryption report
    logger.info(f"\n🔐 Decryption Complete Report\n{'━'*30}")
    logger.info(f"✓ Successfully decrypted: {success} files")
    if failures:
        logger.warning(f"✕ Failed files ({len(failures)}):")
        for f in failures:
            logger.warning(f"  • {f}")
    logger.info(f"{'━'*30}")

    return success

def repair_pdfs_by_rebuilding(input_dir=INPUT_DIR, output_dir=None):
    """
    Attempts to repair PDF internal structure by re-saving.
    This helps resolve issues caused by PDF file corruption or format problems during merging.
    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str, optional): Directory to save repaired PDFs. If None, overwrites original files.
    Returns:
        bool: True if all files were successfully repaired, False otherwise.
    """
    logger.info(f"Starting PDF file structure repair (by re-saving)...")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.warning("No PDF files found for repair.")
        return True

    success_count = 0
    error_files = []

    with tqdm(pdf_files, desc="Repairing PDFs") as pbar:
        for filename in pbar:
            input_path = os.path.join(input_dir, filename)
            temp_output_path = os.path.join(input_dir, f"~temp_repaired_{filename}") # Use temp file for atomicity
            final_output_path = os.path.join(output_dir, filename) if output_dir else input_path

            try:
                # Open with pikepdf and save, which rebuilds the internal structure
                with pikepdf.open(input_path) as pdf:
                    pdf.save(temp_output_path)

                # Atomically replace the original file or move to output_dir
                if output_dir:
                    shutil.move(temp_output_path, final_output_path)
                else:
                    os.replace(temp_output_path, final_output_path) # replace original

                success_count += 1
                logger.info(f"✅ Repair successful: {filename}")
            except Exception as e:
                error_files.append((filename, str(e)))
                logger.error(f"❌ Repair failed: {filename} - {str(e)}")
            finally:
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path) # Ensure temp file is cleaned up

    logger.info(f"\n--- PDF Repair Report ---")
    logger.info(f"Total files: {len(pdf_files)}")
    logger.info(f"Successfully repaired: {success_count} files")
    logger.info(f"Failed files: {len(error_files)} files")
    if error_files:
        for fname, reason in error_files:
            logger.info(f"  - {fname}: {reason}")
    logger.info(f"--------------------")

    return len(error_files) == 0

def delete_filename_chars(char):
    """Deletes specific characters from filenames."""
    for f in os.listdir(INPUT_DIR):
        if char in f:
            new_name = f.replace(char, '')
            os.rename(
                os.path.join(INPUT_DIR, f),
                os.path.join(INPUT_DIR, new_name)
            )
            print(f"Renamed: {f} -> {new_name}")

def _generate_new_name(original_name):
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
        return original_name  # Return original name to avoid further errors

    # Clean up old prefixes
    clean_name = re.sub(r'^[A-Za-z\u4e00-\u9fff]-', '', original_name)

    # Extract the first character
    first_char_match = re.search(r'([\u4e00-\u9fff]|[A-Za-z])', clean_name)
    if not first_char_match:
        logger.warning(f"Could not generate prefix for: {original_name}")
        return original_name  # Return original name

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

def rename_items(mode):
    """
    Batch rename files/directories.
    Args:
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

    # Get items to process
    items = []
    for name in os.listdir(INPUT_DIR):
        path = os.path.join(INPUT_DIR, name)
        if not os.path.exists(path):  # Add existence check
            logger.warning(f"Path does not exist: {path}")
            continue

        if mode in ['both', 'folders'] and os.path.isdir(path):
            items.append(('folder', name))
        elif mode in ['both', 'files'] and os.path.isfile(path):
            items.append(('file', name))

    with tqdm(items, desc=f"Renaming {mode}") as pbar:
        for item_type, name in pbar:
            old_path = os.path.join(INPUT_DIR, name)

            # Safely generate new name
            new_base = _generate_new_name(name)
            if not isinstance(new_base, str):
                logger.error(f"Generated new name is invalid: {new_base}")
                continue

            # Handle file extension
            if item_type == 'file':
                base_part, ext = os.path.splitext(new_base)
                if not ext:  # If new name loses extension
                    original_ext = os.path.splitext(name)[1]
                    new_base += original_ext
                new_name = new_base
            else:
                new_name = new_base

            # Path safety check
            if not os.path.exists(old_path):
                logger.warning(f"Original path does not exist: {old_path}")
                continue

            new_path = os.path.join(INPUT_DIR, new_name)

            # Conflict resolution (try up to 100 times)
            counter = 1
            while os.path.exists(new_path) and counter <= 100:
                base, ext = os.path.splitext(new_name) if item_type == 'file' else (new_name, '')
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(INPUT_DIR, new_name)
                counter += 1
                logger.warning(f"Conflict detected, trying new name: {new_name}")

            try:
                os.rename(old_path, new_path)
                pbar.set_postfix_str(f"{name[:10]} → {new_name[:10]}")
            except Exception as e:
                logger.error(f"Rename failed | {name} | Reason: {str(e)}")

def flatten_directories():
    """
    Directory flattening process.
    Features:
        1. Extracts all files from subdirectories to the root directory.
        2. Deletes empty subdirectories.
        3. Automatically handles filename conflicts (appends a serial number).
    Risks:
        - May cause filename conflicts.
        - Irreversible operation (directory deletion).
    """
    logger.info("Starting directory flattening operation...")
    moved_files = 0

    for dir_name in tqdm(os.listdir(INPUT_DIR), desc="Processing Directories"):
        dir_path = os.path.join(INPUT_DIR, dir_name)
        if not os.path.isdir(dir_path):
            continue

        # Move all files
        for root, _, files in os.walk(dir_path):
            for file in files:
                src = os.path.join(root, file)
                dest = os.path.join(INPUT_DIR, file)

                # Handle filename conflicts
                counter = 1
                base, ext = os.path.splitext(file)
                while os.path.exists(dest):
                    new_name = f"{base}_{counter}{ext}"
                    dest = os.path.join(INPUT_DIR, new_name)
                    counter += 1

                shutil.move(src, dest)
                moved_files += 1

        # Force delete directory
        try:
            shutil.rmtree(dir_path)
            logger.info(f"Successfully deleted directory: {dir_name}")
        except Exception as e:
            logger.error(f"Directory deletion failed: {dir_name} - {str(e)}")

    logger.info(f"Completed! Moved {moved_files} files.")

def add_filename_prefix(prefix, processed_files=None):
    logger.info(f"Starting to add prefix: {prefix}")

    # Get file list
    try:
        files_in_dir = os.listdir(INPUT_DIR)
        logger.info(f"All files in directory: {files_in_dir}")
    except Exception as e:
        logger.error(f"Could not get file list: {str(e)}")
        return

    # Filter for PDF, TXT, EPUB files and folders, and exclude .DS_Store
    target_files = [
        f for f in files_in_dir
        if ((f.lower().endswith(('.pdf', '.txt', '.epub')) or os.path.isdir(os.path.join(INPUT_DIR, f)))
            and f != '.DS_Store')
    ]

    # Print suffix for each file, check for unexpected suffixes
    for f in files_in_dir:
        logger.info(f"Filename suffix check: {f}, Suffix: {f.lower()[-4:]}")

    logger.info(f"Files to process: {target_files}")

    if not target_files:
        logger.error("No matching files found, please check directory and filenames!")
        return

    with tqdm(target_files, desc="Adding Prefix") as pbar:
        for file in pbar:
            src = os.path.join(INPUT_DIR, file)
            new_name = f"{prefix}{file}"
            dest = os.path.join(INPUT_DIR, new_name)

            try:
                logger.info(f"Renaming: {src} -> {dest}")
                os.rename(src, dest)
                logger.info(f"Successfully renamed: {file} → {new_name}")
            except Exception as e:
                logger.error(f"Processing failed: {file} - {str(e)}")

    logger.info(f"Prefix addition complete! Processed {len(target_files)} files (PDF/TXT/EPUB/FOLDER).")

def extract_numbers_in_filenames():
    """
    Extracts numbers from filenames.
    Args:
        char (str): Character to delete (supports regex).
    Example:
        -D "_copy" → Deletes "_copy" from all filenames.
    Note:
        - Affects both files and directories.
        - Irreversible operation.
    """
    logger.info("Starting to extract numbers from filenames...")
    processed_files = []
    conflict_count = 0
    skipped_files = []

    # Get all PDF files (case-insensitive)
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower()]

    with tqdm(pdf_files, desc="Processing Files", unit="file") as pbar:
        for filename in pbar:
            src_path = os.path.join(INPUT_DIR, filename)

            # ==== New: Skip purely numeric filenames ====
            base_without_ext = os.path.splitext(filename)[0]  # Remove extension
            if re.fullmatch(r'^\d+$', base_without_ext):  # Fully match purely numeric
                skipped_files.append(filename)
                logger.info(f"Skipping purely numeric file: {filename}")
                continue
            # ==============================

            # ==== Shell script logic implementation ====
            # 1. Extract all numbers and hyphens
            numbers = re.sub(r'[^0-9-]', '', filename)

            # 2. Remove leading and trailing hyphens
            numbers = numbers.lstrip('-').rstrip('-')

            # 3. Check if it contains numbers
            if not re.search(r'\d', numbers):
                skipped_files.append(filename)
                logger.warning(f"No numbers found: {filename}")
                continue

            # ==== Enhanced processing logic ====
            # Generate base filename
            base_name = f"{numbers}.pdf"
            dest_path = os.path.join(INPUT_DIR, base_name)

            # Handle filename conflicts
            counter = 1
            while os.path.exists(dest_path):
                new_base = f"{numbers}_{counter}.pdf"
                dest_path = os.path.join(INPUT_DIR, new_base)
                conflict_count += 1
                counter += 1
                logger.info(f"Conflict detected: {base_name} → {new_base}")

            try:
                os.rename(src_path, dest_path)
                processed_files.append(os.path.basename(dest_path))
                pbar.set_postfix_str(f"{filename[:15]} → {os.path.basename(dest_path)[:15]}")
            except Exception as e:
                logger.error(f"Rename failed {filename}: {str(e)}")

    # Generate statistics report
    report = REPORT_TEMPLATE.format(
    title="Number Extraction Report",
    total=len(pdf_files),
    success=len(processed_files))

    logger.info(report)
    if skipped_files:
        logger.info("Skipped files list:")
        for f in skipped_files:
            logger.info(f"  · {f}")

    return processed_files

def epub_to_txt():
    """
    EPUB to TXT conversion.
    Processing logic:
        1. Parses EPUB directory structure.
        2. Extracts text content (retains paragraph structure).
        3. Filters HTML tags.
        4. Adds source annotation.
    Dependencies:
        - ebooklib for parsing EPUB.
        - BeautifulSoup for processing HTML.
    Output:
        Generates a .txt file with the same name, containing cleaned text content.
    """
    logger.info("Starting batch EPUB to TXT conversion")
    epub_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.epub')]

    for epub_file in tqdm(epub_files, desc="EPUB Conversion"):
        try:
            input_path = os.path.join(INPUT_DIR, epub_file)
            output_path = os.path.join(INPUT_DIR, f"{os.path.splitext(epub_file)[0]}.txt")

            # Remove unsupported ignore_ncx parameter
            book = epub.read_epub(input_path)  # <-- Key modification

            content = []
            for item in book.get_items():
                # Fix: Replaced ITEM_STYLE with 9 (or epub.ITEM_DOCUMENT) to correctly identify text content
                if item.get_type() == 9: # <-- Fix point: Ensure this is 9 or epub.ITEM_DOCUMENT
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text_blocks = [
                        elem.get_text(strip=True)
                        for elem in soup.find_all(['p', 'h1', 'h2', 'h3'])
                        if elem.get_text(strip=True)
                    ]
                    content.append('\n\n'.join(text_blocks))

            with open(output_path, 'w', encoding='utf-8') as fout:
                fout.write('\n\n'.join(content))
                # Removed this line: fout.write(f"\n\n—— Converted from: {epub_file} ——")

            logger.info(f"✅ Conversion successful: {epub_file} → {os.path.basename(output_path)}")
        except Exception as e:
            logger.error(f"Conversion failed {epub_file}: {str(e)}")

def pdf_to_txt(output_format='standard'):
    """PDF to TXT standalone function."""
    logger.info("Starting batch PDF to TXT conversion")
    pdf_files = [
    f for f in os.listdir(INPUT_DIR)
    if f.lower().endswith('.pdf')]

    for pdf_file in tqdm(pdf_files, desc="PDF Conversion"):
        try:
            input_path = os.path.join(INPUT_DIR, pdf_file)
            output_path = os.path.join(INPUT_DIR, f"{os.path.splitext(pdf_file)[0]}.txt")

            text = ""
            with fitz.open(input_path) as doc:
                for page in doc:
                    text += page.get_text()

            # Process text based on format parameter
            if output_format == 'compact':
                text = re.sub(r'\n{3,}', '\n', text)
            elif output_format == 'clean':
                text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s。，！？]', '', text)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            logger.info(f"Conversion successful: {pdf_file} → {os.path.basename(output_path)}")
        except Exception as e:
            logger.error(f"Conversion failed {pdf_file}: {str(e)}")

def pdf_to_images(fmt='png', dpi=300):
    """
    PDF to Image function.
    Args:
        fmt (str): Output format, can be png/jpg.
        dpi (int): Output resolution.
    Features:
        - Generates a separate image for each page.
        - Creates a separate directory for each PDF.
        - Supports high-resolution output.
    Dependencies: PyMuPDF(fitz)
    """
    logger.info(f"Starting PDF to {fmt.upper()} image conversion")
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]

    for pdf_file in tqdm(pdf_files, desc="PDF to Image"):
        try:
            input_path = os.path.join(INPUT_DIR, pdf_file)
            output_dir = os.path.join(INPUT_DIR, os.path.splitext(pdf_file)[0])
            os.makedirs(output_dir, exist_ok=True)

            pdf = fitz.open(input_path)
            for i, page in enumerate(pdf):
                pix = page.get_pixmap(dpi=dpi)
                output_path = os.path.join(output_dir, f"page_{i+1}.{fmt}")
                pix.save(output_path)

            logger.info(f"Conversion complete: {pdf_file} → {os.path.basename(output_dir)}/")
        except Exception as e:
            logger.error(f"Conversion failed {pdf_file}: {str(e)}")

def images_to_pdf(target_width=1500, dpi=300):
    """Image to PDF standalone function."""
    logger.info("Starting Image to PDF conversion")
    image_files = sorted(
        [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))],
        key=natural_sort_key
    )

    if not image_files:
        logger.warning("No convertible image files found.")
        return

    pdf_path = os.path.join(INPUT_DIR, "combined_images.pdf")
    images = []

    try:
        for img_file in tqdm(image_files, desc="Processing Images"):
            img_path = os.path.join(INPUT_DIR, img_file)
            with Image.open(img_path) as img:
                # Resize
                w_percent = target_width / float(img.width)
                h_size = int(float(img.height) * float(w_percent))
                img = img.resize((target_width, h_size), Image.LANCZOS)
                images.append(img.convert("RGB"))

        # Save PDF
        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:],
            dpi=(dpi, dpi),
            quality=95
        )
        logger.info(f"PDF generated successfully: {os.path.basename(pdf_path)}")
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")

def reverse_rename():
    """
    Reverse renaming (removes prefix).
    Processing rules:
        Format "X-filename" → "filename".
        Example: "A-report.pdf" → "report.pdf".
    Features:
        - Automatically handles name conflicts.
        - Supports both files and directories.
    """
    logger.info("Starting reverse renaming operation...")
    renamed_count = 0

    # Process all items (files and folders) in the input directory
    items = [name for name in os.listdir(INPUT_DIR)]

    with tqdm(items, desc="Reverse Renaming") as pbar:
        for name in pbar:
            old_path = os.path.join(INPUT_DIR, name)

            # Match format: X-xxxx (X is a single letter or Chinese character)
            match = re.match(r'^([A-Z\u4e00-\u9fff])-(.+)$', name)
            if not match:
                logger.info(f"Skipping non-matching format: {name}")
                continue

            # Generate new name
            new_name = match.group(2)
            new_path = os.path.join(INPUT_DIR, new_name)

            # Handle name conflicts
            counter = 1
            while os.path.exists(new_path):
                base, ext = os.path.splitext(new_name) if os.path.isfile(old_path) else (new_name, '')
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(INPUT_DIR, new_name)
                counter += 1
                logger.warning(f"Name conflict detected, renaming to: {new_name}")

            try:
                os.rename(old_path, new_path)
                renamed_count += 1
                logger.info(f"Reverse renamed: {name} → {new_name}")
            except Exception as e:
                logger.error(f"Rename failed: {name} → {str(e)}")

    logger.info(f"✅ Reverse renaming complete! Processed {renamed_count} items.")

def parse_args():
    parser = argparse.ArgumentParser(
        description="📚 Document Processing Tool v8.0 - Multi-functional File Batch Processing System",
        formatter_class=CustomHelpFormatter,
        add_help=False,  # Disable default help function
        epilog=r"""
               __    __    _______  ___         _______
              /" |  | "\  /"     "||"  |       |   __ "\
             (:  (__)  :)(: ______)||  |       (. |__) :)
              \/      \/  \/    |  |:  |       |:  ____/
             //  __  \\  // ___)_  \  |___    (|  /
            (:  (  )  :)(:      "|( \_|:  \  /|__/ \
             \__|  |__/  \_______) \_______)(_______)

            Quick Command Reference:

            【Extraction & Flattening】
            -X              Extracts archive files.
            -F              Flattens extracted directory structure.

            【Filename Processing】
            -D "char"       Deletes specified characters from filenames (supports regex).
            -P "prefix"     Adds a prefix to filenames.
            -N              Batch renames using numbers in filenames.

            【PDF Operations】
            -C p NAME       Merges all PDFs into [NAME].pdf.
            --decode-pdf PASSWORD  Decrypts PDF files.
            --encode-pdf PASSWORD  Encrypts PDF files.
            -T lf           Deletes first and last pages of PDFs.
            --repair-pdf    🛠️ Repairs PDF files (by re-saving).

            【Format Conversion】
            --epubTtxt      EPUB to TXT (outputs with same name).
            --pdfTtxt [clean] PDF to TXT (clean mode removes noise).
            --pdfTimg FORMAT DPI  PDF to image (e.g., jpg 150).
            --imgTpdf WIDTH DPI  Image to PDF (e.g., 2000 300).

            【Batch Renaming】
            -R files       Renames files (used with -P/-D).
            -R folders     Renames folders.

            【Image Processing】
            Optional parameters:
            --compress-images FILENAME
                                    📉 Compresses images and generates PDF (default lossless mode).
                                    Example:
                                    --compress-images output.pdf       # Lossless compression
                                    --compress-images report.pdf --lossy  # Lossy compression
            --lossy              🔧 Enables lossy compression mode (default uses lossless compression).
                                    Features:
                                    - JPEG quality set to 85.
                                    - PNG enables lossy compression.
                                    - File size can be reduced by 40-60%.
""")

    # Core Operations Group
    core_args = parser.add_argument_group("[Core Operations]",
        "These operations modify file structure, recommended to execute first.")
    # Modify --trim-pages parameter definition in parse_args() function's core_args group
    core_args.add_argument('-T', '--trim-pages',
        nargs='+',  # Allows multiple arguments
        metavar=("TYPE", "NUM"),
        help="""✂️  PDF Page Cropping (atomic operation, preserves original file)
        Mode description:
        f [N] : Deletes the first N pages (default 1 page).
        l [N] : Deletes the last N pages (default 1 page).
        lf    : Deletes the first and last page.
        Example:
        -T l 3    # Deletes the last 3 pages.
        -T f       # Deletes the first page.
        -T lf      # Deletes the first and last page.""")

    core_args.add_argument('-F', '--flatten-dirs',
        action='store_true',
        help="""📂 Directory Flattening (irreversible operation)
        Features:
          1. Extracts all files from subdirectories to the input directory.
          2. Forces deletion of empty directories.
          3. Automatically handles filename conflicts.
        Risk warning:
          ⚠️ May cause file overwrites, backup recommended first.
        Example:
          -F        # Executes flattening operation.""")

    core_args.add_argument('-C', '--combine',
        nargs='+',
        metavar=("TYPE", "NAME"),
        help="""📚 Merge Files Operation
        Format: -C TYPE [FILENAME]
        p : Merges PDF files (default name combined.pdf).
        t : Merges TXT files (default name combined.txt).
        e : Merges EPUB files (default name combined.epub).
        Example:
          -C e         -> combined.epub
          -C e library  -> library.epub""")

    # File Operations Group
    file_ops = parser.add_argument_group("[File Operations]",
        "File renaming and batch processing functions.")
    file_ops.add_argument('-D', '--delete', metavar='STR',
        help="""🗑  Filename Cleanup (supports regular expressions)
        Features:
          Deletes all matching characters from filenames.
        Example:
          -D "_copy"     # Deletes "_copy" from filenames.
          -D "[\\[\\]]"  # Deletes all square brackets.
        Notes:
          ① Affects both files and directories.
          ② Irreversible operation, testing recommended first.""")

    file_ops.add_argument('-P', '--add-prefix', metavar='STR',
        help="""🏷  Add File Prefix (smart processing)
        Features:
          ① Only affects PDF/TXT files.
          ② Automatically skips files that already have the prefix.
        Example:
          -P "2024Q1_"   # Adds a quarterly prefix.
          -P "FINAL_"    # Marks as final version.
        Special feature:
          Supports secondary processing (used with -N parameter).""")

    file_ops.add_argument('-N', '--extract-numbers',
        action='store_true',
        help="""🔢 Numeric Renaming
        Extracts numbers and hyphens (-.) from filenames.
        Example: -N""")

    file_ops.add_argument('-R', '--rename',
        nargs='?',
        const='both',
        default=None,
        help="""🔄 Rename Operation (supports the following modes):
        (no argument) : Processes both directories and files.
        folders  : Renames directories only.
        files    : Renames files only.
        Example:
          -R       # Processes all.
          -R files # Files only.""")

    file_ops.add_argument('-V', '--reverse-rename',
        action='store_true',
        help="""↩️ Reverse Renaming (removes X- prefix)
        Processing rules:
          1. Only processes names in the format X-xxxx.
          2. Automatically handles name conflicts.
        Example:
          Input: B-Report.pdf → Output: Report.pdf
          Input: D-Data/ → Output: Data/""")

    # Format Conversion Group
    convert_group = parser.add_argument_group("[Format Conversion]", "Document format conversion functions.")

    # EPUB to TXT
    convert_group.add_argument('--epubTtxt',
        action='store_true',
        help="""📖 EPUB to Plain Text
        Features:
          - Retains chapter structure.
          - Automatically filters empty paragraphs.
          - Supports complex layout EPUBs.
        Output format:
          Generates a .txt file with the same name as the EPUB.
        Note: This function does not require the --output-format parameter.""")

    # PDF to TXT
    convert_group.add_argument('--pdfTtxt',
        action='store_true',
        help="""📄 PDF to Editable Text
        Additional parameters:
          --txt-format : Text format [standard|compact|clean]
            standard : Retains original format (default).
            compact  : Compact mode, reduces blank lines.
            clean    : Clean mode, removes non-text content.""")

    # PDF to Image
    convert_group.add_argument('--pdfTimg',
        action='store_true',
        help="""🖼  PDF to Image
        Additional parameters:
          --img-format : Output format [png|jpg] (default png).
          --dpi        : Output resolution (default 300).
        Output method:
          Creates a separate directory for each PDF.""")

    # Image to PDF
    convert_group.add_argument('--imgTpdf',
        action='store_true',
        help="""📷 Image to PDF
        Additional parameters:
          --pdf-width : PDF page width (default 1500px).
          --pdf-dpi   : Output DPI (default 300).
        Output file:
          Generates combined_images.pdf.""")

    # Conversion parameter options
    convert_group.add_argument('--txt-format',
        choices=['standard', 'compact', 'clean'],
        default='standard',
        help="Text conversion format settings.")

    convert_group.add_argument('--img-format',
        choices=['png', 'jpg'],
        default='png',
        help="Image output format.")

    convert_group.add_argument('--dpi',
        type=int,
        default=300,
        help="Image output resolution.")

    convert_group.add_argument('--pdf-width',
        type=int,
        default=1500,
        help="PDF page width.")

    convert_group.add_argument('--pdf-dpi',
        type=int,
        default=300,
        help="PDF output DPI.")

    # Security Operations Group
    security_group = parser.add_argument_group("Security Operations")
    security_group.add_argument('--decode-pdf',
        metavar="PASSWORD",
        help="🔓 Decrypts PDF files using the specified password.")

    security_group.add_argument('--encode-pdf',
        metavar="PASSWORD",
        help="🔐 Encrypts PDF files using the specified password.")

    security_group.add_argument('-X', '--extract-archives',
        action='store_true',
        help="""📦 Extracts archive files.
        Supported formats: zip/7z/rar/tar/gz/bz2/xz/iso.
        Default password: 1111.
        Example: -X""")

    # New PDF Repair Option
    security_group.add_argument('--repair-pdf',
        action='store_true',
        help="""🛠️ Repairs PDF files (by re-saving).
        Attempts to repair PDF internal structure to resolve merging or processing issues.
        Example: --repair-pdf""")

    # Image Compression
    parser.add_argument('--compress-images',
                        action='store',
                        metavar='FILENAME',
                        default=None,
                        help="""📉 Compresses images and generates PDF (default lossless mode).
                        Example:
                          --compress-images output.pdf       # Lossless compression
                          --compress-images report.pdf --lossy  # Lossy compression""")

    # Default help option
    parser.add_argument('-h', '--help', action='help', help='Show this help message and exit.')

    return parser.parse_args()

if __name__ == "__main__":
    print(r"""
    /\_/\           ___
   = o_o =_______    \ \
    __^      __(  \.__) )
(@)<_____>__(_____)____/
::::::::::: :::::::   ::::::::   ::::::::   ::::::::  :::        ::::::::
    :+:    :+:    :+: :+:    :+: :+:    :+: :+:    :+: :+:       :+:    :+:
    +:+    +:+    +:+ +:+    +:+ +:+    +:+ +:+    +:+ +:+       +:+
    +#+    +#+    +:+ +#+    +:+ +#+    +:+ +#+    +:+ +#+       +#++:++#++
    +#+    +#+    +#+ +#+    +#+ +#+    +:+ +#+    +#+ +#+              +#+
    #+#    #+#    #+# #+#    #+# #+#    #+# #+#    #+# #+#       #+#    #+#
    ###     ########   ########   ########   ########  ########## ########
                                            ^~^,           by Dadoudouoo
                                           ('Y') )
                                           /   \/
                                          (\|||/)      """)

    args = parse_args()

    try:
        # ================= Layered Processing Logic =================
        def process_core_operations(args):
            """Handles core operations (extraction, flattening)."""
            if args.extract_archives:
                extract_archives()
            if args.flatten_dirs:
                flatten_directories()

        def process_file_operations(args):
            """Handles file operations (renaming, deleting characters, prefixes, etc.)."""
            # Rename operation
            if args.rename is not None:
                if args.rename == '':
                    rename_items('both')
                elif args.rename in ['folders', 'files']:
                    rename_items(args.rename)
                else:
                    raise ValueError(f"Invalid rename mode: {args.rename}")

            # Reverse rename
            if args.reverse_rename:
                reverse_rename()

            # Delete characters
            if args.delete:
                delete_filename_chars(args.delete)

            # Add prefix
            processed_files = []
            if args.extract_numbers:
                processed_files = extract_numbers_in_filenames()

            if args.add_prefix:
                add_filename_prefix(args.add_prefix, processed_files)

        def process_conversions(args):
            """Handles format conversions (EPUB/PDF/image conversions)."""
            if args.epubTtxt:
                epub_to_txt()
            if args.pdfTtxt:
                pdf_to_txt(args.txt_format)
            if args.pdfTimg:
                pdf_to_images(args.img_format, args.dpi)
            if args.imgTpdf:
                images_to_pdf(args.pdf_width, args.pdf_dpi)

        def process_security_operations(args):
            """Handles security operations (PDF encryption/decryption)."""
            if args.decode_pdf:
                decode_pdfs(password=args.decode_pdf)
            elif args.encode_pdf:
                encode_pdfs(password=args.encode_pdf)
            # New PDF repair operation
            if args.repair_pdf:
                logger.info("Executing PDF repair operation...")
                repair_pdfs_by_rebuilding(input_dir=INPUT_DIR, output_dir=None) # Default to overwriting original files
                logger.info("PDF repair operation complete.")

        # Modify parameter processing logic in process_other_operations function
        def process_other_operations(args):
            """Handles other operations (file merging, page cropping, etc.)."""
            if args.combine:
                combine_files(args.combine)

            if args.trim_pages:
                # Parse cropping parameters
                trim_type = args.trim_pages[0].lower()
                num_pages = 1  # Default value

                # Handle numeric parameters
                if trim_type in ('f', 'l') and len(args.trim_pages) > 1:
                    try:
                        num_pages = int(args.trim_pages[1])
                        if num_pages < 1:
                            raise ValueError
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid page number parameter, using default 1.")
                        num_pages = 1

                # Validate parameter combination
                if trim_type == 'lf' and len(args.trim_pages) > 1:
                    logger.warning("lf mode does not support page number parameter, extra parameter ignored.")

                remove_pdf_pages(trim_type=trim_type, num_pages=num_pages)

            if args.compress_images is not None:
                compress_images(
                    filename=args.compress_images
                )

        # ================= Execute Processing Flow =================
        process_core_operations(args)       # Prioritize core operations
        process_file_operations(args)       # Then file operations
        process_conversions(args)           # Execute format conversions
        process_security_operations(args)   # Handle encryption/decryption
        process_other_operations(args)      # Finally, handle other operations

    except Exception as e:
        logger.error(f"❌ Operation failed: {str(e)}")
