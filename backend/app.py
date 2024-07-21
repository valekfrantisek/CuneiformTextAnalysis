""" This is a Flask app for the CuneiformTextAnalysis project. It facilitates functions for the cuneiform transliterated text analysis. """

version = '0.0.1'
authors = ['František Válek']
project_name = 'CuneiformTextAnalysis'
project_git = 'https://github.com/valekfrantisek/CuneiformTextAnalysis'
project_web = 'https://dh-tools.cz/CuneiformTextAnalysis'

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from cachelib import SimpleCache
import os
import logging
import traceback
import json
from io import BytesIO, StringIO
import uuid
import pandas as pd
import time

from docx_processor import extract_data_from_composition_document
from cuneiform_analyser import analyse_signs_used, extract_attested_forms_from_manuscript, analyse_words_used, get_table_of_words, oraccise_document

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
            
            cache.set(f'upload_{upload_id}', json.dumps(processed_file), timeout=3600)  # timeout in seconds
            
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
    
    cache.set(f'signs_{upload_id}', json.dumps(signs_used_in_manuscript), timeout=3600)

    response_data = {'success': True, 'analysis': signs_used_in_manuscript, 'syntax_errors': manuscript_syntax_error_report}
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    # TODO: CONTINUE HERE!! Add to JS!!
    
    return response_json, 200


@app.route('/analyzeWordsAction/<upload_id>', methods=['POST'])
def analyze_words(upload_id):
    processed_file = json.loads(cache.get(f'upload_{upload_id}'))
    if not processed_file:
        return jsonify({'error': 'File not found'}), 404
    
    reconstructed_words_used_in_dataset, partially_reconstructed_words_used_in_dataset, preserved_words_used_in_dataset, full_words_used_in_dataset = analyse_words_used(input_data=processed_file)
    
    word_forms_table_data = get_table_of_words(reconstructed_words_used_in_dataset, partially_reconstructed_words_used_in_dataset, preserved_words_used_in_dataset, full_words_used_in_dataset)
    
    cache.set(f'words_{upload_id}', json.dumps(word_forms_table_data), timeout=3600)
    
    response_data = {'success': True, 'analysis': word_forms_table_data, 'syntax_errors': 'None'}
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    return response_json, 200


@app.route('/analyzeGlossaryAction/<upload_id>', methods=['POST'])
def analyze_glossary(upload_id):
    processed_file = json.loads(cache.get(f'upload_{upload_id}'))
    if not processed_file:
        return jsonify({'error': 'File not found'}), 404
    
    glossary_dict = extract_attested_forms_from_manuscript(input_data=processed_file)
    
    cache.set(f'glossary_{upload_id}', json.dumps(glossary_dict), timeout=3600)
    
    response_data = {'success': True, 'analysis': glossary_dict, 'syntax_errors': 'None'}
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    return response_json, 200


def change_False_True_str_to_bool(input_values: list):
    output = []
    for string in input_values:
        if string.lower() == 'true':
            value = True
        elif string.lower() == 'false':
            value = False
        else:
            value = 'Not valid'
        
        output.append(value)

    return output
        

@app.route('/analyzeORACCAction/<upload_id>', methods=['POST'])
def analyze_ORACC(upload_id):
    processed_file = json.loads(cache.get(f'upload_{upload_id}'))
    if not processed_file:
        return jsonify({'error': 'File not found'}), 404
    
    data = request.json
    
    parameters = change_False_True_str_to_bool([data.get('obverseReverse'), data.get('columns')])
    rec_vers = parameters[0]
    cols = parameters[1]
    
    oracc_output_data, error_report = oraccise_document(processed_file, rec_vers=rec_vers, cols=cols)
    
    cache.set(f'oracc_{upload_id}', json.dumps(oracc_output_data), timeout=3600)    
    
    oracc_data_as_html = oracc_output_data.replace('\n', '<br>')
    oracc_data_as_html = f'<p class="oracc-output">{oracc_data_as_html}</p>'
    
    response_data = {'success': True, 'analysis': oracc_output_data, 'as_html_data': oracc_data_as_html, 'syntax_errors': error_report}
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    return response_json, 200

""" DOWNLOAD FUNCTIONS --------------------------------------------------------------- """

@app.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    data = json.loads(cache.get(filename))
    if data is None:
        return jsonify({'error': 'File not found or expired'}), 404
    
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'sign'
    df.reset_index(inplace=True)
    
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )
    
    
@app.route('/download_xlsx/<filename>', methods=['GET'])
def download_xlsx(filename):
    data = json.loads(cache.get(filename))
    if data is None:
        return jsonify({'error': 'File not found or expired'}), 404
    
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'sign'
    df.reset_index(inplace=True)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    
    return Response(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
    )


@app.route('/download_atf/<filename>', methods=['GET'])
def download_atf_file(filename):
    data = json.loads(cache.get(filename))
    if data is None:
        return jsonify({'error': 'File not found or expired'}), 404
    
    output = StringIO()
    output.write(data)
        
    output.seek(0)
    
    return Response(
        output,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}.atf'}
    )


if __name__ == '__main__':
    app.run(debug=True)