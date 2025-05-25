import os
import re
import argparse
import logging
from pathlib import Path

# Import necessary modules directly
from modules import iso_creator
from modules import file_organizer
from modules import archive_extractor
from modules import filename_manager
from modules import image_converter
from modules import text_converter
from modules import pdf_processor
from modules import file_combiner
from modules import pdf_security_processor

INPUT_DIR = os.getcwd()
PROCESSED_FILES_DIR = os.path.join(INPUT_DIR, "processed_files")
DEBUG = True

DEFAULT_ORGANIZE_EXTENSIONS = {'.pdf', '.epub', '.txt'}

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
        for text in re.split(r'(\d+)', s)
    ]

class CustomHelpFormatter(argparse.RawTextHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=100)

def parse_args():
    parser = argparse.ArgumentParser(
        description="📚 Document Processing Tool v8.0 - Multi-functional File Batch Processing System",
        formatter_class=CustomHelpFormatter,
        add_help=False
    )

    # Core Operations Group
    core_args = parser.add_argument_group("[Core Operations]",
        "These operations modify file structure, recommended to execute first.")
    core_args.add_argument('-T', '--trim-pages', '-TP',
        nargs='+',
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

    core_args.add_argument('-F', '--flatten-dirs', '-FD',
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

    core_args.add_argument('-C', '--combine', '-CB',
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
    file_ops.add_argument('-D', '--delete', '-DL', metavar='STR',
        help="""🗑  Filename Cleanup (supports regular expressions)
        Features:
          Deletes all matching characters from filenames.
        Example:
          -D "_copy"     # Deletes "_copy" from filenames.
          -D "[\\[\\]]"  # Deletes all square brackets.
        Notes:
          ① Affects both files and directories.
          ② Irreversible operation, testing recommended first.""")

    file_ops.add_argument('-P', '--add-prefix', '-AP', metavar='STR',
        help="""🏷  Add File Prefix (smart processing)
        Features:
          ① Only affects PDF/TXT files.
          ② Automatically skips files that already have the prefix.
        Example:
          -P "2024Q1_"   # Adds a quarterly prefix.
          -P "FINAL_"    # Marks as final version.
        Special feature:
          Supports secondary processing (used with -N parameter).""")

    file_ops.add_argument('-N', '--extract-numbers', '-EN',
        action='store_true',
        help="""🔢 Numeric Renaming
        Extracts numbers and hyphens (-.) from filenames.
        Example: -N""")

    file_ops.add_argument('-R', '--rename', '-RN',
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

    file_ops.add_argument('-V', '--reverse-rename', '-RR',
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

    convert_group.add_argument('--epubTtxt', '-ET',
        action='store_true',
        help="""📖 EPUB to Plain Text
        Features:
          - Retains chapter structure.
          - Automatically filters empty paragraphs.
          - Supports complex layout EPUBs.
        Output format:
          Generates a .txt file with the same name as the EPUB.
        Note: This function does not require the --output-format parameter.""")

    convert_group.add_argument('--pdfTtxt', '-PT',
        action='store_true',
        help="""📄 PDF to Editable Text
        Additional parameters:
          --txt-format : Text format [standard|compact|clean]
            standard : Retains original format (default).
            compact  : Compact mode, reduces blank lines.
            clean    : Clean mode, removes non-text content.""")

    convert_group.add_argument('--pdfTimg', '-PI',
        action='store_true',
        help="""🖼  PDF to Image
        Additional parameters:
          --img-format : Output format [png|jpg] (default png).
          --dpi        : Output resolution (default 300).
        Output method:
          Creates a separate directory for each PDF.""")

    convert_group.add_argument('--imgTpdf', '-IP',
        action='store_true',
        help="""📷 Image to PDF
        Additional parameters:
          --pdf-width : PDF page width (default 1500px).
          --pdf-dpi   : Output DPI (default 300).
        Output file:
          Generates combined_images.pdf.""")

    convert_group.add_argument('--txt-format', '-TF',
        choices=['standard', 'compact', 'clean'],
        default='standard',
        help="Text conversion format settings.")

    convert_group.add_argument('--img-format', '-IF',
        choices=['png', 'jpg'],
        default='png',
        help="Image output format.")

    convert_group.add_argument('--dpi', '-DP',
        type=int,
        default=300,
        help="Image output resolution.")

    convert_group.add_argument('--pdf-width', '-PW',
        type=int,
        default=1500,
        help="PDF page width.")

    convert_group.add_argument('--pdf-dpi', '-PD',
        type=int,
        default=300,
        help="PDF output DPI.")

    # Security Operations Group
    security_group = parser.add_argument_group("Security Operations")
    security_group.add_argument('--decode-pdf', '-DCP',
        metavar="PASSWORD",
        help="🔓 Decrypts PDF files using the specified password.")

    security_group.add_argument('--encode-pdf', '-ECP',
        metavar="PASSWORD",
        help="🔐 Encrypts PDF files using the specified password.")

    security_group.add_argument('-X', '--extract-archives', '-XA',
        action='store_true',
        help="""📦 Extracts archive files.
        Supported formats: zip/7z/rar/tar/gz/bz2/xz/iso.
        Default password: 1111.
        Example: -X""")

    security_group.add_argument('--repair-pdf', '-RPDF',
        action='store_true',
        help="""🛠️ Repairs PDF files (by re-saving).
        Attempts to repair PDF internal structure to resolve merging or processing issues.
        Example: --repair-pdf""")

    parser.add_argument('--compress-images', '-CI',
                        action='store',
                        metavar='FILENAME',
                        default=None,
                        help="""📉 Compresses images and generates PDF (default lossless mode).
                        Example:
                          --compress-images output.pdf       # Lossless compression
                          --compress-images report.pdf --lossy  # Lossy compression""")
    
    # Adding --lossy argument as it was in the epilog but not defined
    parser.add_argument('--lossy', '-LSS',
                        action='store_true',
                        help="""🔧 Enables lossy compression mode (default uses lossless compression).
                        Features:
                        - JPEG quality set to 85.
                        - PNG enables lossy compression.
                        - File size can be reduced by 40-60%%.""") # Escaped %

    parser.add_argument('--iso-creator', '-ISO',
                        action='store_true',
                        help="""💿 Creates ISO files from subfolders in the current directory.
                        This function is specific to macOS and requires 'hdiutil'.
                        Example: --iso-creator""")

    parser.add_argument('--pdf-page-remover', '-PPR',
                        nargs='+',
                        type=int,
                        metavar='PAGE_NUMBERS',
                        help="""🗑️ Removes specific pages from PDFs.
                        Provide 1-indexed page numbers separated by spaces.
                        Example: --pdf-page-remover 1 3 5  # Removes 1st, 3rd, 5th pages""")

    parser.add_argument('--file-organizer', '-FO',
                        action='store_true',
                        help="""🗂️ Organizes files in the current directory into subfolders
                        based on common substrings in their filenames.
                        Targets PDF, EPUB, and TXT files by default.
                        Example: --file-organizer""")

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
    +#+    +#+    +#+ +#+    +#+ +#+    +#+ +#+    +#+ +#+              +#+
    #+#    #+#    #+# #+#    #+# #+#    #+# #+#    #+# #+#       #+#    #+#
    ###     ########   ########   ########   ########  ########## ########
                                            ^~^,           by Dadoudouoo
                                           ('Y') )
                                           /   \/
                                          (\|||/)      """)

    args = parse_args()

    try:
        def process_core_operations(args):
            if args.extract_archives:
                archive_extractor.extract_archives(INPUT_DIR)
            if args.flatten_dirs:
                filename_manager.flatten_directories(INPUT_DIR)
            if args.iso_creator:
                logger.info("Executing ISO creation operation...")
                iso_creator.process_subfolders_to_iso([os.getcwd()], output_base_dir=os.getcwd())
                logger.info("ISO creation operation complete.")


        def process_file_operations(args):
            if args.rename is not None:
                if args.rename == '':
                    filename_manager.rename_items(INPUT_DIR, 'both')
                elif args.rename in ['folders', 'files']:
                    filename_manager.rename_items(INPUT_DIR, args.rename)
                else:
                    raise ValueError(f"Invalid rename mode: {args.rename}")

            if args.reverse_rename:
                filename_manager.reverse_rename(INPUT_DIR)

            if args.delete:
                filename_manager.delete_filename_chars(INPUT_DIR, args.delete)

            processed_files = []
            if args.extract_numbers:
                processed_files = filename_manager.extract_numbers_in_filenames(INPUT_DIR)

            if args.add_prefix:
                filename_manager.add_filename_prefix(INPUT_DIR, args.add_prefix, processed_files)

            if args.file_organizer:
                logger.info("Executing file organization operation...")
                file_organizer.organize_files_by_group(INPUT_DIR, DEFAULT_ORGANIZE_EXTENSIONS)
                logger.info("File organization operation complete.")


        def process_conversions(args):
            if args.epubTtxt:
                text_converter.epub_to_txt(INPUT_DIR, PROCESSED_FILES_DIR)
            if args.pdfTtxt:
                text_converter.pdf_to_txt(INPUT_DIR, PROCESSED_FILES_DIR, args.txt_format)
            if args.pdfTimg:
                image_converter.pdf_to_images(INPUT_DIR, PROCESSED_FILES_DIR, args.img_format, args.dpi)
            if args.imgTpdf:
                image_converter.images_to_pdf(INPUT_DIR, PROCESSED_FILES_DIR, args.pdf_width, args.pdf_dpi)

        def process_security_operations(args):
            if args.decode_pdf:
                pdf_security_processor.decode_pdfs(INPUT_DIR, args.decode_pdf)
            elif args.encode_pdf:
                pdf_security_processor.encode_pdfs(INPUT_DIR, PROCESSED_FILES_DIR, args.encode_pdf)
            if args.repair_pdf:
                logger.info("Executing PDF repair operation...")
                pdf_processor.repair_pdfs_by_rebuilding(input_dir=INPUT_DIR, output_dir=PROCESSED_FILES_DIR)
                logger.info("PDF repair operation complete.")

        def process_other_operations(args):
            if args.combine:
                file_combiner.combine_files(INPUT_DIR, PROCESSED_FILES_DIR, args.combine)

            if args.trim_pages:
                trim_type = args.trim_pages[0].lower()
                num_pages = 1

                if trim_type in ('f', 'l') and len(args.trim_pages) > 1:
                    try:
                        num_pages = int(args.trim_pages[1])
                        if num_pages < 1:
                            raise ValueError
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid page number parameter, using default 1.")

                if trim_type == 'lf' and len(args.trim_pages) > 1:
                    logger.warning("lf mode does not support page number parameter, extra parameter ignored.")

                pdf_processor.remove_pdf_pages(INPUT_DIR, PROCESSED_FILES_DIR, trim_type=trim_type, num_pages=num_pages)
            
            if args.compress_images is not None:
                image_converter.compress_images(INPUT_DIR, PROCESSED_FILES_DIR, filename=args.compress_images)
            
            if args.pdf_page_remover:
                logger.info(f"Executing specific PDF page removal operation for pages: {args.pdf_page_remover}")
                pages_to_remove_0_indexed = [p - 1 for p in args.pdf_page_remover if p > 0]
                
                if not pages_to_remove_0_indexed:
                    logger.warning("No valid page numbers provided for --pdf-page-remover (pages must be > 0).")
                else:
                    pdf_processor.process_pdfs_for_specific_page_removal_in_directory(
                        Path(INPUT_DIR),
                        pages_to_remove_0_indexed,
                        Path(PROCESSED_FILES_DIR)
                    )
                logger.info("Specific PDF page removal operation complete.")

        process_core_operations(args)
        process_file_operations(args)
        process_conversions(args)
        process_security_operations(args)
        process_other_operations(args)

    except Exception as e:
        logger.error(f"❌ Operation failed: {str(e)}")