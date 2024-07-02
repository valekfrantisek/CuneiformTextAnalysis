from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import logging
from docx_processor import extract_data_from_composition_document
import traceback

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*"}})

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
            file.save(file_path)
            logging.info(f'File saved: {file_path}')
            
            layout = request.form.get('layout', 'default')
            logging.info(f'Selected layout: {layout}')
            
            content = extract_data_from_composition_document(file_path, layout)
            response = make_response(jsonify({'success': True, 'content': content, 'layout': layout}))
            response.headers['Location'] = request.url  # Prevent redirect
            return response, 200
        
        logging.error('File type not allowed')
        return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        logging.error(f'Error in upload_file: {str(e)}')
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

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