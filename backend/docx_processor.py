from docx import Document


def load_document(input_path):
    """ This function loads the document for further analysis. """
    manuscript_document = Document(input_path)
    return manuscript_document


def sum_line_designation(manuscript:str, column_rec_ver:str, line_num:str):
    """ This function summarises line designation - manuscript ID, column/recto/verso, and the line number. """
    return f'{manuscript} {column_rec_ver} {line_num}'


def assign_type(formatted_data:dict):
    """ This function assigns a type of analysed text based on the concise formatting. """
    text = formatted_data['text']
    if formatted_data['italic']:
        return {'text': text, 'type': 'syllabic'}
    elif formatted_data['superscript'] and ':' in text:
        return {'text': text, 'type': 'manuscript designation'}
    elif formatted_data['small caps']:
        if formatted_data['superscript']:
            return {'text': text, 'type': 'post/determinative'}
        if formatted_data['subscript']:
            return {'text': text, 'type': 'sign number'}
        else:
            return {'text': text, 'type': 'ideo/logographic'}
    elif formatted_data['uppercase']:
        return {'text': text, 'type': 'sign_value'}
    else:
        # print('Check this one', text)
        return {'text': text, 'type': 'other'}


def get_formatted_text_from_cell(input_cell_data):
    """ This function collects data on formatting from the line data from the formatted docx document."""
    formatted_data = [] 
    for paragraph in input_cell_data.paragraphs:
        for run in paragraph.runs:
            text = run.text
            italic = run.italic
            uppercase = text.isupper()
            superscript = run.font.superscript
            subscript = run.font.subscript
            small_caps = run.font.small_caps
            formatted_data.append({
                'text': text,
                'italic': italic,
                'uppercase': uppercase,
                'superscript': superscript,
                'subscript': subscript,
                'small caps': small_caps
            })
    return formatted_data


def simple_print_line_data(formatted_line_data:list):
    """ This function simply prints line data without further information. """
    line_text = ''
    for element in formatted_line_data:
        line_text += element['text']
    
    return line_text


def get_formatted_text_from_table(input_table, column_rec_ver:str):
    """ This function analyses formatted text from the whole table. """
    full_formated_data_of_one_manuscript = {}
    note_num = 1
    
    for row in input_table.rows:
        for i, cell in enumerate(row.cells):
            if cell.text == '':
                """ If the cell is empty it is either in line for translation, or the next cell is a note for the manuscript. """
                if i == 1:
                    translation_row = True
                    #print('translation row')
                    next_cell_possible_note = False
                    continue
                elif i == 0:
                    next_cell_possible_note = True
                else:
                    continue
                
            elif i == 1 and next_cell_possible_note:
                """ If this is note to the manuscript, record it as such. """
                full_formated_data_of_one_manuscript[f'note {note_num}'] = cell.text
                next_cell_possible_note = False
                note_num += 1
                
            elif i == 0:
                """ If cell 0 is not empty, then it is a line designation. """
                line_number_designation = cell.text
                if '/' in line_number_designation:
                    """ This means the text belongs to more manuscripts --> it will have to be divided later. """
                    # TODO: place the division here or somewhere later (more likely!)
                    continue
                line_number_elements = line_number_designation.split(' ')
                line_number = line_number_elements[-1]
                manuscript = line_number_elements[0]
                full_line_designation = sum_line_designation(manuscript=manuscript, column_rec_ver=column_rec_ver, line_num=line_number)
                # print(full_line_designation)
                
                next_cell_possible_note = False
                
            else:
                """ If it is the second cell and it has content and it is not the note, it is finally the text! """
                cell_data = get_formatted_text_from_cell(input_cell_data=cell)
                line_primary_analysis = []
                for element in cell_data:
                    element_info = assign_type(element)
                    line_primary_analysis.append(element_info)
                    
                # NOTE: record the line data with the line number
                full_formated_data_of_one_manuscript[full_line_designation] = line_primary_analysis
                
                next_cell_possible_note = False
                            
    return full_formated_data_of_one_manuscript


def get_headings_and_tables_from_document(input_document):
    """ This function gets headings and tables from DOCX document. """
    document_data = []
    table_idx = 0
    for paragraph in input_document.paragraphs:
        if paragraph.style.name.startswith('Heading'):
            heading_text = paragraph.text
            # Find next table
            while table_idx < len(input_document.tables):
                next_elem = paragraph._element.getnext()
                if next_elem is not None and next_elem.tag.endswith('tbl'):
                    table = input_document.tables[table_idx]
                    document_data.append({
                        'heading': heading_text,
                        'table': table
                    })
                    table_idx += 1
                    break
                table_idx += 1
                
    return document_data


def extract_data_from_composition_document(input_document:Document):
    """ This function analyses document that contains transcriptions of cuneiform texts.
    
    It counts with headers that indicate the column of the composition and the transcription must be within two column table.
    The headings must be unique.
    Every second row must be empty (to include translation of the text in the future).
    
    Other functions will be prepared that deal with other outlines and other types of texts. """

    document_headings_et_tables = get_headings_and_tables_from_document(input_document=input_document)
    
    complete_analysed_document = {}
    
    for section in document_headings_et_tables:
        heading = section['heading']
        table = section['table']

        column_rec_ver = heading
    
        full_formated_data_of_one_manuscript = get_formatted_text_from_table(input_table=table, column_rec_ver=column_rec_ver)
        
        complete_analysed_document[heading] = full_formated_data_of_one_manuscript
        
        # NOTE: printing individual lines in simple format
        for line in full_formated_data_of_one_manuscript:
            if 'note' in line:
                print(full_formated_data_of_one_manuscript[line])
            else:
                # print(full_formated_data_of_one_manuscript[line])
                line_text = simple_print_line_data(full_formated_data_of_one_manuscript[line])
                print(line, line_text)
                
    return complete_analysed_document