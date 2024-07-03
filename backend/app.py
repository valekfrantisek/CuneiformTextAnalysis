from flask import Flask, request, jsonify, send_from_directory, make_response, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
from docx_processor import extract_data_from_composition_document
import traceback
import json
from io import BytesIO

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*", "expose_headers": "Content-Type"}})

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug('Upload endpoint called')
    try:
        if 'file' not in request.files:
            logging.error('No file part in the request')
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            logging.error('No selected file')
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            file_buffer = BytesIO()
            file.save(file_buffer)
            file_buffer.seek(0)
            logging.info(f'File uploaded to memory')
        
            layout = request.form.get('layout', 'default')
            # layout = 'lines'
            logging.info(f'Selected layout: {layout}')
            
            logging.debug('Starting content extraction')
            content = extract_data_from_composition_document(file_buffer, layout)
            # content = 'ulalal'
            logging.debug(f"Content extracted, size: {len(str(content))} bytes")

            response_data = {'success': True, 'content': content, 'layout': layout}
            response_json = json.dumps(response_data, ensure_ascii=False)

            logging.debug("Sending response")
        
            return response_json, 200
    
    except Exception as e:
        logging.error(f'Error in upload_file: {str(e)}')
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        logging.debug("Upload function completed")

@app.route('/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text', '')
    #TODO: implement data_analysis
    result = {
        'text_length': len(text),
        'analysis': 'Placeholder for Akkadian text analysis'
    }
    return jsonify(result), 200

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)