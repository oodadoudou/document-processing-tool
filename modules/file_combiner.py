import os
import re
import logging
import time
from tqdm import tqdm
import pikepdf

from modules import report_generator

logger = logging.getLogger(__name__)
if not logger.handlers:
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
        for text in re.split(r'(\d+)', s)
    ]

def combine_files(input_dir: str, output_dir: str, args_list: list) -> None:
    """
    Main merge function (supports multiple file types).
    Args:
        input_dir (str): The directory containing the files to be merged.
        output_dir (str): The directory where the merged file will be saved.
        args_list (list): Command-line argument list, e.g., ['e', 'output'] to merge EPUBs to output.epub
    """
    if not args_list:
        logger.error("❌ Merge operation requires at least a type parameter.")
        return

    success_files = []
    error_files = []
    start_time = time.time()

    try:
        file_type = args_list[0].lower()
        base_name = args_list[1] if len(args_list) > 1 else "combined"
        ext_map = {
            'p': '.pdf',
            't': '.txt'
        }

        if file_type not in ext_map:
            logger.error(f"❌ Invalid file type: {file_type} (Supported types: {', '.join(ext_map.keys())})")
            return

        ext = ext_map[file_type]
        os.makedirs(output_dir, exist_ok=True)
        output_name = f"{base_name}{ext}" if not base_name.endswith(ext) else base_name
        output_path = os.path.join(output_dir, output_name)


        files = sorted(
            [f for f in os.listdir(input_dir) if f.endswith(ext)],
            key=natural_sort_key
        )

        if not files:
            logger.error("❌ No files found for merging.")
            return

        logger.info(f"📚 Starting to merge {ext.upper()} files -> {output_path}")
        logger.info("📄 File processing order:")
        for i, f in enumerate(files, 1):
            logger.info(f"{i:02d}. {f}")

        handlers = {
            'p': _combine_pdfs,
            't': _combine_txts,
        }
        
        if file_type in handlers:
            handlers[file_type](input_dir, files, output_path, success_files, error_files)
        else:
            logger.error(f"❌ No handler defined for file type: {file_type}")
            return

        report_generator.generate_merge_report(
            output_name=output_name,
            files=files,
            success_files=success_files,
            error_files=error_files,
            start_time=start_time
        )

    except Exception as e:
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        logger.error(f"❌ Merge operation abnormally terminated: {type(e).__name__} - {str(e)}")
        report_generator.generate_partial_report(
            success_files=success_files,
            error_files=error_files,
            exception=e
        )


def _combine_pdfs(input_dir: str, files: list, output_path: str, success_files: list, error_files: list) -> None:
    """
    Core logic for merging PDF files, now using pikepdf for merging.
    pikepdf is generally more robust than PyPDF2 for handling complex or corrupted PDFs.
    """
    new_pdf = pikepdf.new()
    try:
        for f in tqdm(files, desc="Merging PDFs"):
            file_path = os.path.join(input_dir, f)
            try:
                with pikepdf.open(file_path) as src_pdf:
                    new_pdf.pages.extend(src_pdf.pages)
                success_files.append(f)
            except Exception as e:
                error_detail = str(e).split('\n')[0]
                error_files.append((f, error_detail))
                logger.error(f"❌ PDF merge failed: {f} | {error_detail}")

        new_pdf.save(output_path)
    finally:
        pass

def _combine_txts(input_dir: str, files: list, output_path: str, success_files: list, error_files: list) -> None:
    """Core logic for merging TXT files."""
    with open(output_path, 'w', encoding='utf-8') as out:
        for f in tqdm(files, desc="Merging TXTs"):
            file_path = os.path.join(input_dir, f)
            try:
                with open(file_path, 'r', errors='replace') as infile:
                    content = infile.read()
                    out.write(content + '\n')
                success_files.append(f)
            except Exception as e:
                error_detail = str(e).split('\n')[0]
                error_files.append((f, error_detail))
                logger.error(f"❌ TXT merge failed: {f} | {error_detail}")