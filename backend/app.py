# backend/app.py - Main Flask application server
import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    from modules import filename_manager
    from modules import text_converter
    from modules import pdf_security_processor
    from modules import pdf_processor
    from modules import iso_creator
    from modules import image_converter
    from modules import file_combiner 
    from modules import file_organizer 
    from modules import folder_processor
except ImportError:
    from modules import filename_manager
    from modules import text_converter
    from modules import pdf_security_processor
    from modules import pdf_processor
    from modules import iso_creator
    from modules import image_converter
    from modules import file_combiner
    from modules import file_organizer
    from modules import folder_processor

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
module_logger = logging.getLogger(__name__)

# Health check endpoint for monitoring
@app.route('/api/health', methods=['GET'])
def health_check():
    module_logger.info("Health check endpoint called.")
    return jsonify({"status": "ok", "message": "Backend is running!"}), 200

# --- Filename Manager API Endpoints ---
@app.route('/api/filename/add_prefix', methods=['POST'])
def api_add_filename_prefix():
    module_logger.info("API call to /api/filename/add_prefix received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        prefix = data.get('prefix')
        processed_files_list = data.get('processed_files_list', None)
        if not directory_path or prefix is None: return jsonify({"status": "error", "message": "Missing 'directory_path' or 'prefix'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.add_filename_prefix_api(directory_path, prefix, processed_files_list)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Prefix addition process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_add_filename_prefix")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/delete_chars', methods=['POST'])
def api_delete_filename_chars():
    module_logger.info("API call to /api/filename/delete_chars received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        char_pattern = data.get('char_pattern')
        if not directory_path or char_pattern is None: return jsonify({"status": "error", "message": "Missing 'directory_path' or 'char_pattern'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.delete_filename_chars_api(directory_path, char_pattern)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Character deletion process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_delete_filename_chars")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/rename_items', methods=['POST'])
def api_rename_items():
    module_logger.info("API call to /api/filename/rename_items received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        mode = data.get('mode')
        if not directory_path or not mode: return jsonify({"status": "error", "message": "Missing 'directory_path' or 'mode'."}), 400
        if mode not in ['both', 'folders', 'files']: return jsonify({"status": "error", "message": "Invalid mode."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.rename_items_api(directory_path, mode)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Item renaming process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_rename_items")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/flatten_dirs', methods=['POST'])
def api_flatten_directories():
    module_logger.info("API call to /api/filename/flatten_dirs received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        if not directory_path: return jsonify({"status": "error", "message": "Missing 'directory_path'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.flatten_directories_api(directory_path)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Directory flattening process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_flatten_directories")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/extract_numbers', methods=['POST'])
def api_extract_numbers_in_filenames():
    module_logger.info("API call to /api/filename/extract_numbers received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        if not directory_path: return jsonify({"status": "error", "message": "Missing 'directory_path'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.extract_numbers_in_filenames_api(directory_path)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Number extraction process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_extract_numbers_in_filenames")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/reverse_rename', methods=['POST'])
def api_reverse_rename():
    module_logger.info("API call to /api/filename/reverse_rename received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        if not directory_path: return jsonify({"status": "error", "message": "Missing 'directory_path'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.reverse_rename_api(directory_path)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Reverse renaming process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_reverse_rename")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/filename/add_suffix', methods=['POST'])
def api_add_filename_suffix():
    module_logger.info("API call to /api/filename/add_suffix received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        directory_path = data.get('directory_path')
        suffix = data.get('suffix')
        processed_files_list = data.get('processed_files_list', None)
        if not directory_path or suffix is None: return jsonify({"status": "error", "message": "Missing 'directory_path' or 'suffix'."}), 400
        if not os.path.isdir(directory_path): return jsonify({"status": "error", "message": f"Directory not found: {directory_path}"}), 404
        result = filename_manager.add_filename_suffix_api(directory_path, suffix, processed_files_list)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Suffix addition process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_add_filename_suffix")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- Text Converter API Endpoints ---
@app.route('/api/text/epub_to_txt', methods=['POST'])
def api_epub_to_txt():
    module_logger.info("API call to /api/text/epub_to_txt received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir') 
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = text_converter.epub_to_txt_api(input_dir, output_dir)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "EPUB to TXT conversion process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_epub_to_txt")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/text/pdf_to_txt', methods=['POST'])
def api_pdf_to_txt():
    module_logger.info("API call to /api/text/pdf_to_txt received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        output_format = data.get('output_format', 'standard') 
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if output_format not in ['standard', 'compact', 'clean']: return jsonify({"status": "error", "message": "Invalid 'output_format'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = text_converter.pdf_to_txt_api(input_dir, output_dir, output_format)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF to TXT conversion process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_pdf_to_txt")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- PDF Security Processor API Endpoints ---
@app.route('/api/pdf/encode', methods=['POST'])
def api_encode_pdfs():
    module_logger.info("API call to /api/pdf/encode received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        password = data.get('password')
        if not all([input_dir, output_dir, password]): return jsonify({"status": "error", "message": "Missing 'input_dir', 'output_dir', or 'password'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = pdf_security_processor.encode_pdfs_api(input_dir, output_dir, password)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF encryption process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_encode_pdfs")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/pdf/decode', methods=['POST'])
def api_decode_pdfs():
    module_logger.info("API call to /api/pdf/decode received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir') 
        password = data.get('password')
        if not input_dir or not password: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'password'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = pdf_security_processor.decode_pdfs_api(input_dir, password)
        status_code = 200 if result.get("success") else 500                                                       
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF decryption process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_decode_pdfs")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- PDF Processor API Endpoints ---
@app.route('/api/pdf/trim_pages', methods=['POST'])
def api_trim_pdf_pages():
    module_logger.info("API call to /api/pdf/trim_pages received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        trim_type = data.get('trim_type', 'f') 
        num_pages_str = data.get('num_pages', '1') 
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        try:
            num_pages = int(num_pages_str)
            if num_pages < 0 : raise ValueError("Number of pages cannot be negative.")
        except ValueError: return jsonify({"status": "error", "message": "Invalid 'num_pages'. Must be a non-negative integer."}), 400
        if trim_type not in ['f', 'l', 'lf']: return jsonify({"status": "error", "message": "Invalid 'trim_type'. Must be 'f', 'l', or 'lf'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = pdf_processor.remove_pdf_pages_api(input_dir, output_dir, trim_type, num_pages)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF page trimming process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_trim_pdf_pages")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/pdf/remove_specific_pages', methods=['POST'])
def api_remove_specific_pdf_pages():
    module_logger.info("API call to /api/pdf/remove_specific_pages received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        pages_to_delete_str = data.get('pages_to_delete_str') 
        if not all([input_dir, output_dir, pages_to_delete_str is not None]): return jsonify({"status": "error", "message": "Missing 'input_dir', 'output_dir', or 'pages_to_delete_str'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = pdf_processor.process_pdfs_for_specific_page_removal_api(input_dir, output_dir, pages_to_delete_str)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Specific PDF page removal process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_remove_specific_pdf_pages")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/pdf/repair', methods=['POST'])
def api_repair_pdfs():
    module_logger.info("API call to /api/pdf/repair received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = pdf_processor.repair_pdfs_by_rebuilding_api(input_dir, output_dir)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF repair process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_repair_pdfs")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- ISO Creator API Endpoint ---
@app.route('/api/iso/create_from_subfolders', methods=['POST'])
def api_create_iso_from_subfolders():
    module_logger.info("API call to /api/iso/create_from_subfolders received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        parent_dirs_list = data.get('parent_dirs_list')
        output_base_dir = data.get('output_base_dir', None) 
        if not parent_dirs_list or not isinstance(parent_dirs_list, list): return jsonify({"status": "error", "message": "Missing or invalid 'parent_dirs_list'."}), 400
        result = iso_creator.process_subfolders_to_iso_api(parent_dirs_list, output_base_dir)
        if result.get("platform_error"): return jsonify({"status": "error", "message": result.get("platform_error"), "details": result}), 405 
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "ISO creation process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_create_iso_from_subfolders")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- Image Converter API Endpoints ---
@app.route('/api/image/compress_to_pdf', methods=['POST'])
def api_compress_images_to_pdf():
    module_logger.info("API call to /api/image/compress_to_pdf received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        output_pdf_filename = data.get('output_pdf_filename', 'compressed_images')
        target_width = data.get('target_width', 1500)
        quality = data.get('quality', 90)
        dpi = data.get('dpi', 300)
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        try:
            target_width = int(target_width); quality = int(quality); dpi = int(dpi)
            if not (target_width > 0 and 0 <= quality <= 100 and dpi > 0): raise ValueError("Invalid image parameters.")
        except ValueError: return jsonify({"status": "error", "message": "Invalid 'target_width', 'quality', or 'dpi' values."}), 400
        result = image_converter.compress_images_api(input_dir, output_dir, output_pdf_filename, target_width, quality, dpi)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Image compression to PDF process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_compress_images_to_pdf")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/image/pdf_to_images', methods=['POST'])
def api_pdf_to_images():
    module_logger.info("API call to /api/image/pdf_to_images received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        fmt = data.get('fmt', 'png')
        dpi = data.get('dpi', 300)
        quality = data.get('quality', 90)
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        try:
            dpi = int(dpi); quality = int(quality)
            if fmt.lower() not in ['png', 'jpg']: raise ValueError("Invalid format")
        except ValueError: return jsonify({"status": "error", "message": "Invalid 'fmt', 'dpi', or 'quality' values."}), 400
        result = image_converter.pdf_to_images_api(input_dir, output_dir, fmt, dpi, quality)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "PDF to images conversion process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_pdf_to_images")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/image/images_to_pdf', methods=['POST'])
def api_images_to_pdf():
    module_logger.info("API call to /api/image/images_to_pdf received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        output_pdf_filename = data.get('output_pdf_filename', 'combined_images')
        target_width = data.get('target_width', 1500)
        dpi = data.get('dpi', 300)
        if not input_dir or not output_dir: return jsonify({"status": "error", "message": "Missing 'input_dir' or 'output_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        try:
            target_width = int(target_width); dpi = int(dpi)
            if not (target_width > 0 and dpi > 0): raise ValueError("Invalid image parameters.")
        except ValueError: return jsonify({"status": "error", "message": "Invalid 'target_width' or 'dpi' values."}), 400
        result = image_converter.images_to_pdf_api(input_dir, output_dir, output_pdf_filename, target_width, dpi)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Images to PDF conversion process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_images_to_pdf")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- File Combiner API Endpoint ---
@app.route('/api/file/combine', methods=['POST'])
def api_combine_files():
    module_logger.info("API call to /api/file/combine received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        output_dir = data.get('output_dir')
        file_type_char = data.get('file_type_char')
        output_base_name = data.get('output_base_name', 'combined_files') # Ensure a default
        if not all([input_dir, output_dir, file_type_char, output_base_name]):
            return jsonify({"status": "error", "message": "Missing one or more required fields: 'input_dir', 'output_dir', 'file_type_char', 'output_base_name'."}), 400
        if file_type_char not in ['p', 't']: return jsonify({"status": "error", "message": "Invalid 'file_type_char'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = file_combiner.combine_files_api(input_dir, output_dir, file_type_char, output_base_name)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "File combination process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_combine_files")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- Folder Processor API Endpoints ---
@app.route('/api/folder/encode_double_compress', methods=['POST'])
def api_encode_folders_double_compression():
    module_logger.info("API call to /api/folder/encode_double_compress received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir')
        password = data.get('password', '1111') 
        if not input_dir: return jsonify({"status": "error", "message": "Missing 'input_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        result = folder_processor.encode_folders_with_double_compression_api(input_dir, password)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Folder encoding process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_encode_folders_double_compression")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

@app.route('/api/folder/decode_double_decompress', methods=['POST'])
def api_decode_folders_double_decompression():
    module_logger.info("API call to /api/folder/decode_double_decompress received.")
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "No JSON data received."}), 400
        input_dir = data.get('input_dir') 
        password = data.get('password', '1111')
        if not input_dir: return jsonify({"status": "error", "message": "Missing 'input_dir'."}), 400
        if not os.path.isdir(input_dir): return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404
        # The API-adapted function for decode now takes only input_dir and password,
        # as output is implicitly input_dir for the Python library version.
        result = folder_processor.decode_folders_with_double_decompression_api(input_dir, password)
        status_code = 200 if result.get("success") else 500
        return jsonify({"status": "success" if result.get("success") else "error", "message": "Folder decoding process finished.", "details": result}), status_code
    except Exception as e:
        module_logger.exception("Error in api_decode_folders_double_decompression")
        return jsonify({"status": "error", "message": f"An unexpected server error: {str(e)}"}), 500

# --- File Organizer API Endpoint ---
@app.route('/api/organizer/organize_by_group', methods=['POST'])
def api_organize_files_by_group():
    module_logger.info("API call to /api/organizer/organize_by_group received.")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data received."}), 400

        input_dir = data.get('input_dir')
        target_extensions_str = data.get('target_extensions_str', ".pdf .epub .txt") # Default extensions

        if not input_dir:
            return jsonify({"status": "error", "message": "Missing 'input_dir'."}), 400
        
        if not os.path.isdir(input_dir):
            return jsonify({"status": "error", "message": f"Input directory not found: {input_dir}"}), 404

        module_logger.info(f"Processing file organization in '{input_dir}' for extensions '{target_extensions_str}'")
        result = file_organizer.organize_files_by_group_api(input_dir, target_extensions_str)
        
        status_code = 200 if result.get("success") else 500
        return jsonify({
            "status": "success" if result.get("success") else "error",
            "message": "File organization process finished.",
            "details": result
        }), status_code

    except Exception as e:
        module_logger.exception("An unexpected error occurred in api_organize_files_by_group.")
        return jsonify({"status": "error", "message": f"An unexpected server error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    module_logger.info("Starting Flask backend server...")
    app.run(host='0.0.0.0', port=5001, debug=False)