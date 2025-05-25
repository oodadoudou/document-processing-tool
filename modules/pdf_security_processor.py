import os
import time
import logging
import pikepdf
from tqdm import tqdm

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def encode_pdfs(input_dir: str, output_dir: str, password: str) -> None:
    """
    PDF Encryption Function (AES-256 Encryption)
    Args:
        input_dir (str): The directory containing the PDF files to encrypt.
        output_dir (str): The directory where the encrypted PDF files will be saved.
        password (str): Encryption password
    Features:
        - Generates an encrypted copy (filename prefixed with "encrypted_").
        - Restricts permissions: disallows printing/copying/modification.
    Dependencies: pikepdf
    """
    logger.info(f"Starting PDF encryption operation with password: {password}")

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logger.error("No PDF files found for encryption.")
        return

    success = 0
    failures = []
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    with tqdm(pdf_files, desc="Encryption Progress", unit="file") as pbar:
        for filename in pbar:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"encrypted_{filename}")

            try:
                with pikepdf.open(input_path) as pdf:
                    pdf.save(output_path, encryption=pikepdf.Encryption(
                        user=password,
                        owner=password,
                        allow=pikepdf.Permissions(
                            accessibility=False,
                            extract=False,
                            modify_annotation=False,
                            print_lowres=False,
                            print_highres=False
                        )
                    ))
                success += 1
                logger.info(f"Encryption successful: {filename} → {output_path}")

            except Exception as e:
                failures.append((filename, str(e)))
                logger.error(f"Encryption failed: {filename} | {str(e)}")

    # Removed: report_generator.generate_report(...)


def decode_pdfs(input_dir: str, password: str) -> int:
    """
    PDF Decryption Function (Supports Brute Force)
    Args:
        input_dir (str): The directory containing the PDF files to decrypt.
        password (str): Decryption password
    Features:
        - Atomic operation (saves to temporary file first).
        - Automatically handles password errors and file corruption.
        - Supports overwriting original files.
    Dependencies: pikepdf
    Returns:
        int: Number of successfully decrypted files.
    """
    logger.info(f"Starting PDF decryption operation with password: {password}")
    success_files_list = []
    failures = []
    start_time = time.time()

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.error("No PDF files found for decryption.")
        return 0

    with tqdm(pdf_files, desc="Decryption Progress", unit="file") as pbar:
        for filename in pbar:
            input_path = os.path.join(input_dir, filename)
            temp_path = os.path.join(input_dir, f"~temp_{filename}")

            try:
                with pikepdf.open(
                    input_path,
                    password=password,
                    allow_overwriting_input=True
                ) as pdf:
                    # If it opens, it's either decrypted or was never encrypted
                    pdf.save(temp_path)
                    os.replace(temp_path, input_path)
                    success_files_list.append(filename)
                    pbar.set_postfix_str(f"Latest Processed: {filename[:15]}")

            except pikepdf.PasswordError:
                failures.append((filename, "Incorrect password"))
                logger.warning(f"Incorrect password for {filename}. Skipping decryption.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                failures.append((filename, str(e)))
                logger.error(f"Error processing {filename}: {type(e).__name__} - {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError as e:
                        logger.warning(f"Could not delete temporary file {temp_path}: {e}")

    return len(success_files_list)