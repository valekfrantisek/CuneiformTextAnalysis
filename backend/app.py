from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from cachelib import SimpleCache
import os
import logging
import traceback
import json
from io import BytesIO
import uuid

from docx_processor import extract_data_from_composition_document
from cuneiform_analyser import analyse_signs_used

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

cache = SimpleCache()

ALLOWED_EXTENSIONS = {'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def log_request_info():
    logging.debug('LOG Before request')

@app.after_request
def log_response_info(request):
    logging.debug('LOG After request')
    return request

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/upload/<layout>', methods=['POST'])
def upload_file(layout):
    logging.debug('Upload called')
    
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
            
            file_content = file.read()
            upload_id = str(uuid.uuid4())
            
            file_buffer = BytesIO(file_content)
            processed_file = extract_data_from_composition_document(file_buffer, layout)
            
            cache.set(f'upload_{upload_id}', json.dumps(processed_file), timeout=60)  # timeout in seconds
            
            logging.debug(f"File content saved to cache with key: upload_{upload_id}")
            
            return jsonify({'message': 'File uploaded successfully', 'upload_id': upload_id, 'filename': filename}), 200
    
    except Exception as e:
        logging.error(f'Error in upload_file: {str(e)}')
        logging.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/analyzeSignsAction/<upload_id>', methods=['POST'])
def analyse_signs(upload_id):
    processed_file = json.loads(cache.get(f'upload_{upload_id}'))
    if not processed_file:
        return jsonify({'error': 'File not found'}), 404
    
    signs_used_in_manuscript, manuscript_syntax_error_report = analyse_signs_used(processed_file)
    if manuscript_syntax_error_report == []:
        manuscript_syntax_error_report = 'None syntax errors encountered in this manuscript during the sign analysis'
    
    print(signs_used_in_manuscript)
    print(manuscript_syntax_error_report)
    
    signs_used_in_manuscript = dict(sorted(signs_used_in_manuscript.items()))

    response_data = {'success': True, 'analysis': signs_used_in_manuscript, 'syntax_errors': manuscript_syntax_error_report}
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    # TODO: CONTINUE HERE!! Add to JS!!
    
    return response_json, 200


if __name__ == '__main__':
    app.run(debug=True)