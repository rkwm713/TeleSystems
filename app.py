from flask import Flask, request, render_template, redirect, url_for, flash, send_file, abort
import os
import uuid
import tempfile
import traceback
import logging
import json
from werkzeug.utils import secure_filename
from processor import process_katapult_json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Create a more persistent upload folder
base_dir = os.path.dirname(os.path.abspath(__file__))
uploads_dir = os.path.join(base_dir, 'uploads')
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

# Application setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size
app.config['UPLOAD_FOLDER'] = uploads_dir
app.config['ALLOWED_EXTENSIONS'] = {'json'}
app.config['DELETE_UPLOADED_JSON'] = True  # Set to False to keep uploaded JSON for debugging

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render the main upload page"""
    return render_template('index.html')

# Debugging route to check what's in the request
@app.route('/debug-request', methods=['POST'])
def debug_request():
    """Debug endpoint to log request details"""
    logger.info("==== DEBUG REQUEST INFO ====")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request form keys: {list(request.form.keys())}")
    logger.info(f"Request files keys: {list(request.files.keys())}")
    
    # Get more details about the files
    for key in request.files:
        file = request.files[key]
        logger.info(f"File '{key}': filename='{file.filename}', content_type='{file.content_type}'")
    
    return "Request details logged. Check server logs."

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    # Log detailed request information
    logger.info(f"Upload request received: content_type={request.content_type}")
    logger.info(f"Request files keys: {list(request.files.keys())}")
    logger.info(f"Request form keys: {list(request.form.keys())}")
    
    # Check if the request has the file part
    if 'json_file' not in request.files:
        # Detailed logging for debugging
        logger.error("'json_file' not found in request.files")
        logger.error(f"Available files: {list(request.files.keys())}")
        logger.error(f"Request content type: {request.content_type}")
        logger.error(f"Form data: {list(request.form.keys())}")
        
        flash('No file part in the request', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['json_file']
    
    # Check if filename is empty
    if file.filename == '':
        flash('No file selected', 'danger')
        logger.warning('Upload attempted with empty filename')
        return redirect(url_for('index'))
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        flash('File type not allowed. Please upload a JSON file.', 'danger')
        logger.warning(f'Upload attempted with disallowed file type: {file.filename}')
        return redirect(url_for('index'))
    
    try:
        # Create unique filenames for uploaded file and output
        unique_id = str(uuid.uuid4())
        secure_name = secure_filename(file.filename)
        
        # Paths for files
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{secure_name}")
        excel_filename = f"make_ready_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        
        # Save the uploaded file
        file.save(json_path)
        logger.info(f'Successfully saved uploaded file: {json_path}')
        
        # Validate JSON file
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                # Verify this is a Katapult file by checking for key structures
                if not all(key in json_data for key in ['nodes', 'connections']):
                    raise ValueError("This does not appear to be a valid Katapult JSON file. Required keys not found.")
        except json.JSONDecodeError:
            flash('The uploaded file is not valid JSON.', 'danger')
            logger.error(f'Invalid JSON format: {json_path}')
            if os.path.exists(json_path):
                os.remove(json_path)
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f'Validation error: {str(e)}', 'danger')
            logger.error(f'JSON validation failed: {str(e)}')
            if os.path.exists(json_path):
                os.remove(json_path)
            return redirect(url_for('index'))
        
        # Process the file
        logger.info(f'Processing file: {json_path}')
        stats = process_katapult_json(json_path, excel_path)
        
        # Check if processing was successful
        if stats.get('status') == 'error':
            flash(f'Processing error: {stats.get("message", "Unknown error")}', 'danger')
            logger.error(f'Processing error: {stats.get("message", "Unknown error")}')
            if os.path.exists(json_path):
                os.remove(json_path)
            return redirect(url_for('index'))
        
        # Clean up the uploaded JSON file if configured to do so
        if app.config['DELETE_UPLOADED_JSON'] and os.path.exists(json_path):
            os.remove(json_path)
            logger.info(f'Removed JSON file: {json_path}')
        
        # Return results page with download link
        logger.info(f'Successfully processed file. Excel report: {excel_path}')
        return render_template('result.html', 
                               excel_filename=excel_filename,
                               stats=stats)
    
    except Exception as e:
        # Log the full error details
        error_detail = traceback.format_exc()
        logger.error(f'Unexpected error: {str(e)}\n{error_detail}')
        
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    """Handle file download"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Validate the file exists
    if not os.path.exists(file_path):
        logger.error(f'Download attempted for non-existent file: {file_path}')
        abort(404, description="File not found")
    
    # Validate that it's an Excel file (for security)
    if not filename.endswith('.xlsx'):
        logger.error(f'Download attempted for non-Excel file: {file_path}')
        abort(403, description="Only Excel files can be downloaded")
    
    logger.info(f'Serving download: {file_path}')
    try:
        return send_file(file_path,
                        as_attachment=True,
                        download_name=filename)
    except Exception as e:
        logger.error(f'Error serving file: {str(e)}')
        abort(500, description="Error serving file")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                           error_code=404, 
                           error_message="File not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                           error_code=500, 
                           error_message="Internal server error"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
