import os
import re
import logging
import time
from PIL import Image, ImageFile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from pathlib import Path
import fitz

try:
    from modules import report_generator
except ImportError:
    import report_generator

# Disable Pillow's DecompressionBombWarning by setting MAX_IMAGE_PIXELS to None
Image.MAX_IMAGE_PIXELS = None
# Allow Pillow to load truncated images, which can sometimes happen with large or corrupted files
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Supported image file extensions for input
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

def natural_sort_key(s: str) -> list:
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

def compress_images(input_dir: str, output_dir: str, filename: str = "compressed", target_width: int = 1500, quality: int = 90, dpi: int = 300, max_workers: int = 5) -> None:
    """
    Super Compression PDF Generation Function (Ultimate Volume Optimization)
    Core optimization techniques:
        - Dual compression pipeline
        - Forced format unification
        - Intelligent chroma subsampling
    Args:
        input_dir (str): The directory containing the image files.
        output_dir (str): The directory where the compressed PDF will be saved.
        filename (str): The base name for the output PDF file.
        target_width (int): The target width for image resizing.
        quality (int): The quality for JPEG compression (0-100). Note: JPEG is a lossy format.
        dpi (int): The DPI for the output PDF.
        max_workers (int): The maximum number of worker threads for parallel compression.
    """
    logger.info(f"Starting image compression and PDF generation in: {input_dir}")

    success_files = []
    error_files = []
    start_time = time.time()

    def _super_compress(img_path):
        try:
            with Image.open(img_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                if img.width > target_width:
                    ratio = target_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((target_width, new_height), Image.LANCZOS)

                temp_path = Path(img_path).parent / f"~temp_{Path(img_path).stem}.jpg"
                img.save(temp_path,
                        quality=quality,
                        optimize=True,
                        subsampling=2,
                        progressive=True)

                os.replace(temp_path, img_path)
                logger.info(f"Successfully compressed and replaced: {Path(img_path).name}")
                return img_path
        except Exception as e:
            logger.error(f"Error during super-compression of {img_path}: {type(e).__name__} - {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return None

    image_files = sorted(
        [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)],
        key=lambda x: natural_sort_key(x)
    )

    if not image_files:
        logger.warning(f"No convertible image files found in '{input_dir}'. Skipping image compression.")
        return

    compressed_image_paths = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(_super_compress,
                             [os.path.join(input_dir, f) for f in image_files]),
                total=len(image_files),
                desc="🔥 Super Compressing"))
        compressed_image_paths = [res for res in results if res is not None]

    if not compressed_image_paths:
        logger.error("All image compressions failed. Cannot generate PDF.")
        return

    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, filename + '.pdf')

    try:
        with Image.open(compressed_image_paths[0]) as first_img:
            other_imgs = []
            for p in compressed_image_paths[1:]:
                try:
                    other_imgs.append(Image.open(p))
                except Exception as e:
                    logger.error(f"Could not open image {p} for PDF merging: {type(e).__name__} - {e}")

            first_img.save(
                pdf_path,
                save_all=True,
                append_images=other_imgs,
                dpi=(dpi, dpi),
                quality=quality,
                subsampling=2,
                progressive=True,
                optimize=True,
                compress_type='zip'
            )

        logger.info(f"✅ Super compression complete | Final size: {os.path.getsize(pdf_path)/1024/1024:.2f}MB. Saved to: {pdf_path}")
        success_files.append(pdf_path)
    except Exception as e:
        logger.error(f"Error generating PDF from compressed images: {type(e).__name__} - {e}")
        error_files.append((filename + '.pdf', str(e)))
    
    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="Image Compression to PDF Report",
        total_processed=len(image_files),
        success_files=success_files,
        error_files=error_files,
        duration=duration
    )


def pdf_to_images(input_dir: str, output_dir: str, fmt: str = 'png', dpi: int = 300, quality: int = 90) -> None:
    """
    PDF to Image function.
    Args:
        input_dir (str): The directory containing the PDF files.
        output_dir (str): The base directory where image output directories will be created.
        fmt (str): Output format, can be 'png' or 'jpg'.
        dpi (int): Output resolution.
        quality (int): Quality for JPG output (0-100). Ignored for PNG.
    """
    logger.info(f"Starting PDF to {fmt.upper()} image conversion in: {input_dir}")
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]

    if not pdf_files:
        logger.warning(f"No PDF files found in '{input_dir}' for image conversion.")
        return

    success_files = []
    error_files = []
    start_time = time.time()

    for pdf_file in tqdm(pdf_files, desc="PDF to Image"):
        try:
            input_path = os.path.join(input_dir, pdf_file)
            
            pdf_base_name = os.path.splitext(pdf_file)[0]
            
            output_dir_for_images = os.path.join(output_dir, pdf_base_name)
            os.makedirs(output_dir_for_images, exist_ok=True)

            pdf = fitz.open(input_path)
            page_success_count = 0
            page_error_count = 0
            for i, page in enumerate(pdf):
                pix = page.get_pixmap(dpi=dpi)
                
                image_filename = f"{pdf_base_name}_{i+1:02d}.{fmt}"
                output_path = os.path.join(output_dir_for_images, image_filename)
                
                try:
                    if fmt.lower() == 'jpg':
                        pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        pil_image.save(output_path, quality=quality, optimize=True, progressive=True)
                    else:
                        pix.save(output_path)
                    logger.debug(f"Saved page {i+1} of {pdf_file} as {image_filename}")
                    page_success_count += 1
                except Exception as save_e:
                    logger.error(f"Error saving image {image_filename} from {pdf_file}: {type(save_e).__name__} - {save_e}")
                    page_error_count += 1
            pdf.close()

            if page_error_count == 0:
                logger.info(f"Conversion complete: {pdf_file} → {os.path.basename(output_dir_for_images)}/ (Images named {pdf_base_name}_XX.{fmt})")
                success_files.append(pdf_file)
            else:
                error_files.append((pdf_file, f"{page_error_count} pages failed to convert"))

        except Exception as e:
            error_msg = str(e).split('\n')[0]
            logger.error(f"Conversion failed for {pdf_file}: {type(e).__name__} - {error_msg}")
            error_files.append((pdf_file, error_msg))

    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="PDF to Image Conversion Report",
        total_processed=len(pdf_files),
        success_files=success_files,
        error_files=error_files,
        duration=duration
    )


def images_to_pdf(input_dir: str, output_dir: str, target_width: int = 1500, dpi: int = 300) -> None:
    """
    Image to PDF conversion.
    Args:
        input_dir (str): The directory containing the image files.
        output_dir (str): The directory where the output PDF will be saved.
        target_width (int): The target width for image resizing before PDF creation.
        dpi (int): The DPI for the output PDF.
    Output file:
        Generates combined_images.pdf.
    """
    logger.info(f"Starting Image to PDF conversion in: {input_dir}")
    image_files = sorted(
        [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)],
        key=natural_sort_key
    )

    if not image_files:
        logger.warning(f"No convertible image files found in '{input_dir}'. Skipping Image to PDF conversion.")
        return

    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "combined_images.pdf")
    images = []

    success_files = []
    error_files = []
    start_time = time.time()

    for img_file in tqdm(image_files, desc="Processing Images"):
        img_path = os.path.join(input_dir, img_file)
        try:
            with Image.open(img_path) as img:
                w_percent = target_width / float(img.width)
                h_size = int(float(img.height) * float(w_percent))
                img = img.resize((target_width, h_size), Image.LANCZOS)
                images.append(img.convert("RGB"))
                success_files.append(img_file)
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            logger.error(f"Could not open or process image {img_file}: {type(e).__name__} - {error_msg}")
            error_files.append((img_file, error_msg))


    if not images:
        logger.error("No images successfully processed for PDF conversion.")
        return

    try:
        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:],
            dpi=(dpi, dpi),
            quality=95
        )
        logger.info(f"PDF generated successfully: {os.path.basename(pdf_path)}. Saved to: {pdf_path}")
    except Exception as e:
        error_msg = str(e).split('\n')[0]
        logger.error(f"Image to PDF conversion failed: {type(e).__name__} - {error_msg}")
        error_files.append(("combined_images.pdf", error_msg))
    
    duration = time.time() - start_time
    report_generator.generate_report(
        report_title="Image to PDF Conversion Report",
        total_processed=len(image_files),
        success_files=[f for f in success_files if f not in [err[0] for err in error_files]],
        error_files=error_files,
        duration=duration
    )