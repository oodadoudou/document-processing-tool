# backend/modules/image_converter.py
import os
import re
import logging
import time
from PIL import Image, ImageFile
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from pathlib import Path
import fitz # PyMuPDF

Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True

module_logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

def natural_sort_key(s: str) -> list:
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r'(\d+)', s)
    ]

def compress_images_api(input_dir: str, output_dir: str, output_pdf_filename: str = "compressed_images", 
                        target_width: int = 1500, quality: int = 90, dpi: int = 300, max_workers: int = 5) -> dict:
    """
    API-adapted: Compresses images and generates a PDF.
    Args:
        input_dir (str): Directory containing image files.
        output_dir (str): Directory to save the compressed PDF.
        output_pdf_filename (str): Base name for the output PDF file (without .pdf extension).
        target_width (int): Target width for image resizing.
        quality (int): Quality for JPEG compression (0-100).
        dpi (int): DPI for the output PDF.
        max_workers (int): Max worker threads for parallel compression.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting image compression and PDF generation from '{input_dir}' to '{output_dir}/{output_pdf_filename}.pdf'")
    messages = []
    processed_image_paths = [] # Store paths of successfully compressed images for PDF creation
    individual_image_success_count = 0
    individual_image_error_count = 0
    individual_image_errors = [] # List of {"file": "...", "error": "..."}
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        image_files = sorted(
            [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)],
            key=natural_sort_key
        )
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not image_files:
        msg = f"No convertible image files found in '{input_dir}'."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_count": 0, "success_count": 0, "error_count": 0}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    total_images_to_process = len(image_files)
    
    # Internal function for compressing a single image
    def _compress_single_image(img_path_str: str):
        img_path = Path(img_path_str)
        try:
            with Image.open(img_path) as img:
                original_mode = img.mode
                if img.mode not in ['RGB', 'L']: # Convert to RGB if not grayscale or RGB
                    img = img.convert('RGB')
                
                if img.width > target_width:
                    ratio = target_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)

                # For this function, we are creating a PDF, so we don't overwrite originals.
                # We'll save compressed versions to a temporary subfolder or pass PIL objects.
                # For simplicity with ThreadPoolExecutor, let's return PIL objects.
                # If memory is a concern for very many large images, saving to temp files is better.
                return img # Return the processed PIL.Image object
        except Exception as e:
            err_msg = f"Error compressing '{img_path.name}': {type(e).__name__} - {str(e).splitlines()[0]}"
            module_logger.error(err_msg)
            return {"file": img_path.name, "error": err_msg} # Return error dict

    processed_pil_images = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_compress_single_image, os.path.join(input_dir, f)) for f in image_files]
        for i, future in enumerate(tqdm(futures, total=total_images_to_process, desc="API Compressing Images", unit="image", disable=True)):
            try:
                result = future.result()
                if isinstance(result, Image.Image):
                    processed_pil_images.append(result)
                    messages.append(f"[SUCCESS] Compressed image: {image_files[i]}")
                    individual_image_success_count +=1
                elif isinstance(result, dict) and "error" in result: # Error dict returned
                    messages.append(f"[ERROR] {result['error']}")
                    individual_image_errors.append(result)
                    individual_image_error_count +=1
                    overall_success = False
            except Exception as e_future: # Should be caught by _compress_single_image, but as a fallback
                err_msg = f"Unexpected error processing future for {image_files[i]}: {e_future}"
                module_logger.error(err_msg)
                messages.append(f"[ERROR] {err_msg}")
                individual_image_errors.append({"file": image_files[i], "error": err_msg})
                individual_image_error_count +=1
                overall_success = False


    if not processed_pil_images:
        msg = "No images were successfully compressed. Cannot generate PDF."
        module_logger.error(msg)
        messages.append(f"[ERROR] {msg}")
        return {
            "success": False, "messages": messages, 
            "total_images_found": total_images_to_process,
            "images_compressed_successfully": individual_image_success_count,
            "image_compression_errors": individual_image_error_count,
            "pdf_generated": False,
            "pdf_path": None,
            "error_details": individual_image_errors
        }

    pdf_filename_with_ext = f"{output_pdf_filename}.pdf" if not output_pdf_filename.lower().endswith('.pdf') else output_pdf_filename
    final_pdf_path = os.path.join(output_dir, pdf_filename_with_ext)
    pdf_generated_successfully = False

    try:
        first_image_to_save = processed_pil_images[0]
        # Ensure first image is RGB for saving as PDF with append_images
        if first_image_to_save.mode != 'RGB':
            first_image_to_save = first_image_to_save.convert('RGB')
            
        images_to_append = []
        for img_obj in processed_pil_images[1:]:
            if img_obj.mode != 'RGB':
                images_to_append.append(img_obj.convert('RGB'))
            else:
                images_to_append.append(img_obj)

        first_image_to_save.save(
            final_pdf_path,
            save_all=True,
            append_images=images_to_append,
            resolution=float(dpi), # PyPDF2/Pillow use resolution for DPI
            quality=quality, # Applies to DCTDecode (JPEG) streams within PDF
            optimize=True
            # subsampling and progressive are JPEG specific, Pillow handles this internally for PDF save
        )
        msg = f"PDF generated successfully: '{pdf_filename_with_ext}'. Saved to: '{final_pdf_path}'"
        module_logger.info(msg)
        messages.append(f"[SUCCESS] {msg}")
        pdf_generated_successfully = True
    except Exception as e_pdf:
        msg = f"Error generating PDF from compressed images: {type(e_pdf).__name__} - {str(e_pdf).splitlines()[0]}"
        module_logger.error(msg)
        messages.append(f"[ERROR] {msg}")
        individual_image_errors.append({"file": "PDF_GENERATION", "error": msg}) # Add PDF gen error
        individual_image_error_count +=1
        overall_success = False
    
    # Close PIL Image objects
    for img_obj in processed_pil_images:
        img_obj.close()

    final_summary_msg = (f"Image compression to PDF finished. Total images found: {total_images_to_process}, "
                         f"Compressed successfully: {individual_image_success_count}, "
                         f"Compression errors: {individual_image_error_count}. PDF Generated: {pdf_generated_successfully}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and pdf_generated_successfully,
        "messages": messages,
        "total_images_found": total_images_to_process,
        "images_compressed_successfully": individual_image_success_count,
        "image_compression_errors": individual_image_error_count,
        "pdf_generated": pdf_generated_successfully,
        "pdf_path": final_pdf_path if pdf_generated_successfully else None,
        "error_details": individual_image_errors
    }


def pdf_to_images_api(input_dir: str, output_dir: str, fmt: str = 'png', dpi: int = 300, quality: int = 90) -> dict:
    """
    API-adapted: PDF to Image function.
    Args:
        input_dir (str): Directory containing PDF files.
        output_dir (str): Base directory for image output subdirectories.
        fmt (str): Output format ('png' or 'jpg').
        dpi (int): Output resolution.
        quality (int): Quality for JPG output (0-100).
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting PDF to {fmt.upper()} conversion from '{input_dir}' to '{output_dir}'. DPI: {dpi}, Quality: {quality if fmt.lower()=='jpg' else 'N/A'}")
    messages = []
    success_conversion_details = [] # List of {"pdf_file": "...", "output_folder": "...", "images_created": count}
    error_conversion_details = []   # List of {"pdf_file": "...", "error": "..."}
    total_pdfs_processed = 0
    total_images_created = 0
    error_count = 0
    overall_success = True

    if fmt.lower() not in ['png', 'jpg']:
        msg = "Invalid image format. Must be 'png' or 'jpg'."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}
    if not (1 <= dpi <= 1200): # Practical DPI range
        msg = "Invalid DPI value. Must be between 1 and 1200."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}
    if fmt.lower() == 'jpg' and not (0 <= quality <= 100):
        msg = "Invalid quality value for JPG. Must be between 0 and 100."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}


    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not pdf_files:
        msg = f"No PDF files found in '{input_dir}' for image conversion."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "total_pdfs_processed": 0, "total_images_created":0, "error_count": 0}

    # output_dir is the base, module function creates subdirs
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create base output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    total_pdfs_to_process = len(pdf_files)

    for pdf_file in tqdm(pdf_files, desc="API PDF to Image", unit="pdf", disable=True):
        input_path = os.path.join(input_dir, pdf_file)
        pdf_base_name = os.path.splitext(pdf_file)[0]
        # Each PDF gets its own subfolder in the output_dir
        current_output_subdir = os.path.join(output_dir, pdf_base_name)
        
        try:
            os.makedirs(current_output_subdir, exist_ok=True)
        except Exception as e_mkdir:
            msg = f"Could not create subdirectory '{current_output_subdir}' for '{pdf_file}': {e_mkdir}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_conversion_details.append({"pdf_file": pdf_file, "error": msg})
            error_count += 1
            overall_success = False
            continue # Skip this PDF

        total_pdfs_processed +=1
        page_conversion_success_count = 0
        page_conversion_error_count = 0
        
        try:
            doc = fitz.open(input_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=dpi)
                image_filename = f"{pdf_base_name}_page_{i+1:03d}.{fmt.lower()}"
                image_output_path = os.path.join(current_output_subdir, image_filename)
                
                try:
                    if fmt.lower() == 'jpg':
                        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img_pil.save(image_output_path, quality=quality, optimize=True, progressive=True)
                    else: # PNG
                        pix.save(image_output_path)
                    page_conversion_success_count += 1
                except Exception as e_save:
                    page_conversion_error_count +=1
                    module_logger.error(f"Error saving page {i+1} of '{pdf_file}' as '{image_filename}': {e_save}")
                    messages.append(f"[ERROR] Saving page {i+1} of '{pdf_file}': {e_save}")
            doc.close()

            if page_conversion_error_count == 0 and page_conversion_success_count > 0:
                msg = f"Successfully converted '{pdf_file}' to {page_conversion_success_count} images in '{current_output_subdir}'."
                module_logger.info(msg)
                messages.append(f"[SUCCESS] {msg}")
                success_conversion_details.append({"pdf_file": pdf_file, "output_folder": current_output_subdir, "images_created": page_conversion_success_count})
                total_images_created += page_conversion_success_count
            elif page_conversion_success_count == 0 and page_conversion_error_count > 0 : # All pages failed
                 msg = f"All pages failed to convert for '{pdf_file}'."
                 module_logger.error(msg)
                 messages.append(f"[ERROR] {msg}")
                 error_conversion_details.append({"pdf_file": pdf_file, "error": "All pages failed conversion."})
                 error_count += 1
                 overall_success = False
            elif page_conversion_error_count > 0: # Partial success
                msg = f"Partially converted '{pdf_file}': {page_conversion_success_count} succeeded, {page_conversion_error_count} failed. Output in '{current_output_subdir}'."
                module_logger.warning(msg)
                messages.append(f"[WARN] {msg}")
                success_conversion_details.append({"pdf_file": pdf_file, "output_folder": current_output_subdir, "images_created": page_conversion_success_count})
                error_conversion_details.append({"pdf_file": pdf_file, "error": f"{page_conversion_error_count} pages failed conversion."})
                total_images_created += page_conversion_success_count
                error_count +=1 # Count as a file-level error if any page fails
                overall_success = False


        except Exception as e_open:
            msg = f"Failed to open or process PDF '{pdf_file}': {type(e_open).__name__} - {str(e_open).splitlines()[0]}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_conversion_details.append({"pdf_file": pdf_file, "error": msg})
            error_count += 1
            overall_success = False

    final_summary_msg = (f"PDF to Image conversion finished. Total PDFs processed: {total_pdfs_processed}, "
                         f"Total images created: {total_images_created}, PDFs with errors: {error_count}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and error_count == 0,
        "messages": messages,
        "total_pdfs_processed": total_pdfs_processed,
        "total_images_created": total_images_created,
        "pdf_error_count": error_count, # Number of PDFs that had at least one error
        "successful_conversions": success_conversion_details,
        "error_details": error_conversion_details
    }


def images_to_pdf_api(input_dir: str, output_dir: str, output_pdf_filename: str = "combined_images", 
                      target_width: int = 1500, dpi: int = 300) -> dict:
    """
    API-adapted: Image to PDF conversion.
    Args:
        input_dir (str): Directory containing image files.
        output_dir (str): Directory to save the output PDF.
        output_pdf_filename (str): Base name for the output PDF.
        target_width (int): Target width for image resizing.
        dpi (int): DPI for the output PDF.
    Returns:
        dict: Operation results.
    """
    module_logger.info(f"API: Starting Image to PDF conversion from '{input_dir}' to '{output_dir}/{output_pdf_filename}.pdf'")
    messages = []
    processed_image_count = 0
    skipped_image_count = 0
    error_image_details = [] # List of {"file": "...", "error": "..."}
    pdf_generated = False
    final_pdf_path = None
    overall_success = True

    if not os.path.isdir(input_dir):
        msg = f"Input directory '{input_dir}' does not exist."
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    try:
        image_files = sorted(
            [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)],
            key=natural_sort_key
        )
    except Exception as e:
        msg = f"Could not read input directory '{input_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    if not image_files:
        msg = f"No convertible image files found in '{input_dir}'."
        module_logger.warning(msg)
        messages.append(f"[WARN] {msg}")
        return {"success": True, "messages": messages, "processed_image_count": 0, "pdf_generated": False}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        msg = f"Could not create output directory '{output_dir}': {e}"
        module_logger.error(msg)
        return {"success": False, "messages": [f"[ERROR] {msg}"], "error_count": 1}

    images_for_pdf = []
    for img_file in tqdm(image_files, desc="API Processing Images for PDF", unit="image", disable=True):
        img_path = os.path.join(input_dir, img_file)
        try:
            with Image.open(img_path) as img:
                # Resize if necessary
                if img.width > target_width:
                    w_percent = target_width / float(img.width)
                    h_size = int(float(img.height) * float(w_percent))
                    img_resized = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
                else:
                    img_resized = img.copy() # Use a copy to avoid issues with closing original
                
                # Convert to RGB for PDF compatibility, especially for the first image
                images_for_pdf.append(img_resized.convert("RGB"))
                processed_image_count += 1
                messages.append(f"[INFO] Processed image: {img_file}")
        except Exception as e_img:
            error_msg = str(e_img).split('\n')[0]
            msg = f"Could not open or process image '{img_file}': {type(e_img).__name__} - {error_msg}"
            module_logger.error(msg)
            messages.append(f"[ERROR] {msg}")
            error_image_details.append({"file": img_file, "error": msg})
            skipped_image_count +=1
            overall_success = False # Mark as not fully successful if any image fails

    if not images_for_pdf:
        msg = "No images were successfully processed for PDF conversion."
        module_logger.error(msg)
        messages.append(f"[ERROR] {msg}")
        return {
            "success": False, "messages": messages, 
            "total_images_found": len(image_files),
            "processed_image_count": processed_image_count,
            "skipped_image_count": skipped_image_count,
            "pdf_generated": False, 
            "error_details": error_image_details
        }

    pdf_filename_with_ext = f"{output_pdf_filename}.pdf" if not output_pdf_filename.lower().endswith('.pdf') else output_pdf_filename
    final_pdf_path = os.path.join(output_dir, pdf_filename_with_ext)

    try:
        first_image = images_for_pdf[0]
        remaining_images = images_for_pdf[1:]
        
        first_image.save(
            final_pdf_path,
            save_all=True,
            append_images=remaining_images if remaining_images else None, # Pass None if no other images
            resolution=float(dpi),
            quality=95 # Pillow's PDF save quality for JPEGs, good default
        )
        pdf_generated = True
        msg = f"PDF generated successfully: '{pdf_filename_with_ext}'. Saved to: '{final_pdf_path}'"
        module_logger.info(msg)
        messages.append(f"[SUCCESS] {msg}")
    except Exception as e_pdf:
        msg = f"Failed to generate PDF from images: {type(e_pdf).__name__} - {str(e_pdf).splitlines()[0]}"
        module_logger.error(msg)
        messages.append(f"[ERROR] {msg}")
        error_image_details.append({"file": "PDF_GENERATION", "error": msg})
        overall_success = False
    
    # Close all opened PIL Image objects to free memory
    for img_obj in images_for_pdf:
        img_obj.close()

    final_summary_msg = (f"Image to PDF conversion finished. Images found: {len(image_files)}, "
                         f"Successfully processed for PDF: {processed_image_count}, Skipped/Errors: {skipped_image_count}. "
                         f"PDF Generated: {pdf_generated}.")
    module_logger.info(final_summary_msg)
    messages.append(f"[INFO] {final_summary_msg}")

    return {
        "success": overall_success and pdf_generated,
        "messages": messages,
        "total_images_found": len(image_files),
        "processed_image_count": processed_image_count,
        "skipped_image_count": skipped_image_count,
        "pdf_generated": pdf_generated,
        "pdf_path": final_pdf_path if pdf_generated else None,
        "error_details": error_image_details
    }
