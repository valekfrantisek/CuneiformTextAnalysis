""" This python script provides functions for app.py. It contains functions that further work with processed file analysed with functions from docx_processor.py """

import os
from collections import defaultdict
from itertools import islice
import pandas as pd
from unidecode import unidecode
import re
import statistics

version = '0.0.1'
authors = ['František Válek']
project_name = 'CuneiformTextAnalysis'
project_web = 'https://github.com/valekfrantisek/CuneiformTextAnalysis'


""" SIGN ANALYSIS -------------------------------------------------------------------------------------------------------------------- """
def normalise_line_text_for_sign_analysis(input_line_data:list):
    final_line = ''
    
    for element in input_line_data:
        if element['type'] == 'manuscript designation':
            continue
        elif element['type'] == 'post/determinative':
            final_line += f'*{element['text']}*'
        else:
            final_line += element['text']
            
    return final_line


def get_signs_from_line(line_text:str, line_id):
    """ Remove longer parts of missing signs and unrecognised sings. """
    line_text = line_text.replace('...', '')
    line_text = line_text.replace('…', '')
    line_text = line_text.replace('(x)', '')
    line_text = line_text.replace('x', '')
    
    signs_in_line = {}
    sign_dict_template = {'preserved': 0, 'partial': 0, 'reconstructed': 0, 'in <>': 0, 'in ()': 0, 'in <<>>': 0}

    enclose_char = ''
    current_state = 'preserved'
    current_sign = ''
    
    syntax_error_report = []
    
    for char in line_text:
        if char in [' ', '.', '-', '[', ']', '⸢', '⸣', '<', '>', '*', '(', ')'] and current_sign:
            if enclose_char == '(':
                if current_sign in signs_in_line:
                    signs_in_line[current_sign]['in ()'] += 1
                    current_sign = ''
                else:
                    signs_in_line[current_sign] = sign_dict_template.copy()
                    signs_in_line[current_sign]['in ()'] += 1
                    current_sign = ''
                
            elif enclose_char == '<':
                if current_sign in signs_in_line:
                    signs_in_line[current_sign]['in <>'] += 1
                    current_sign = ''
                else:
                    signs_in_line[current_sign] = sign_dict_template.copy()
                    signs_in_line[current_sign]['in <>'] += 1
                    current_sign = ''
                    
            elif enclose_char == '<<':
                if current_sign in signs_in_line:
                    signs_in_line[current_sign]['in <<>>'] += 1
                    current_sign = ''
                else:
                    signs_in_line[current_sign] = sign_dict_template.copy()
                    signs_in_line[current_sign]['in <<>>'] += 1
                    current_sign = ''
            else:
                if current_sign in signs_in_line:
                    signs_in_line[current_sign][current_state] += 1
                    current_sign = ''
                else:
                    signs_in_line[current_sign] = sign_dict_template.copy()
                    signs_in_line[current_sign][current_state] += 1
                    current_sign = ''
                
        if char in '- .*':
            continue
        elif char == '[' and current_state == 'preserved':
            current_state = 'reconstructed'
        elif char == ']' and current_state == 'reconstructed':
            current_state = 'preserved'
        elif char == '⸢' and current_state == 'preserved':
            current_state = 'partial'
        elif char == '⸣' and current_state == 'partial':
            current_state = 'preserved'
        elif char == '(':
            enclose_char = '('
        elif char == ')' and enclose_char:
            enclose_char = ''
        elif char == '<':
            if enclose_char == '<':
                enclose_char = '<<'
            else:
                enclose_char = '<'
        elif char == '>':
            enclose_char = ''
        elif char.isalnum() or char == '!' or char == '?' or char == '+' or char =='/':
            current_sign += char
        else:
            syntax_error_report.append({'char': char, 'line_id': line_id})
            print(f'There is an Error in parsing! Probably some syntax error with character "{char}". Check line: {line_id}')
            
    # Collect the final sign
    if current_sign:
        if current_sign in signs_in_line:
                signs_in_line[current_sign][current_state] += 1
                current_sign = ''
        else:
            signs_in_line[current_sign] = sign_dict_template.copy()
            signs_in_line[current_sign][current_state] += 1
            current_sign = ''
            
    return signs_in_line, syntax_error_report


def analyse_signs_used(input_data:dict):
    """ This function provides analysis of signs used in the provided data.
    
    Args:
        input_data (dict): data obtained through function extract_data_from_composition_document().
        use_reconstructions (bool): should reconstructed parts be included into the analysis?
        use_partial_reconstructions (bool): Should partially reconstructed signs be included in the analysis?
        use_uncertainties (bool): should signs with (?) be included in the analysis?
        use_additions (bool): Should the signs added by the editor be used?
        use_erasures (bool): Should the signs "deleted" by the editor should be count?
        
    Returns:
        dict: dictionary of signs with their overall number.
        
    """
    
    signs_used_in_manuscript = {}
    sign_dict_template = {'preserved': 0, 'partial': 0, 'reconstructed': 0, 'in <>': 0, 'in ()': 0, 'in <<>>': 0}
    
    manuscript_syntax_error_report = []
    
    for section in input_data:
        for line in input_data[section]['cuneiform_data']:
            if 'note' in line:
                continue
            else:
                line_data = input_data[section]['cuneiform_data'][line]
                normalised_line = normalise_line_text_for_sign_analysis(input_line_data=line_data)
                line_signs_analysis, line_syntax_error_report = get_signs_from_line(line_text=normalised_line, line_id=line)
                
                manuscript_syntax_error_report.extend(line_syntax_error_report)
                
                for sign in line_signs_analysis:
                    if sign in signs_used_in_manuscript:
                        for state in signs_used_in_manuscript[sign]:
                            signs_used_in_manuscript[sign][state] += line_signs_analysis[sign][state]
                    else:
                        signs_used_in_manuscript[sign] = sign_dict_template.copy()
                        for state in signs_used_in_manuscript[sign]:
                            signs_used_in_manuscript[sign][state] += line_signs_analysis[sign][state]
                    
    return signs_used_in_manuscript, manuscript_syntax_error_report


# TODO: Finish and implement this section on calculating line len from preserved lines.
# def get_signs_from_preserved_line(line_text:str):
#     """ Remove longer parts of missing signs and unrecognised sings. """
#     if '...' in line_text or '…' in line_text:
#         return False
    
#     else:
#         delimiters = ' -.*[]⸢⸣<>()'
#         regex_pattern = f"[{re.escape(delimiters)}]"
#         signs_in_line = re.split(regex_pattern, line_text)
        
#         signs_in_line = [s for s in signs_in_line if s]
                
#         return signs_in_line


# def get_line_length_in_manuscript(input_manuscript:dict):
#     preserved_lines = []
#     preserved_lines_contents = []
#     for col, col_text in input_manuscript.items():
#         for line, line_data  in col_text.items():
#             if 'note' in line:
#                 continue
#             else:
#                 normalised_line = normalise_line_text_for_sign_analysis(input_line_data=line_data)
                
#             line_signs_if_preserved = get_signs_from_preserved_line(line_text=normalised_line)
#             if line_signs_if_preserved:
#                 preserved_lines.append(len(line_signs_if_preserved))
#                 preserved_lines_contents.append(normalised_line)
#             else:
#                 continue
    
#     if preserved_lines == []:
#         print('No preserved lines in this manuscript!')
#     else:
#         average_line_len = statistics.mean(preserved_lines)
#         median_line_len = statistics.median(preserved_lines)
#         shortest_line_len = min(preserved_lines)
#         longest_line_len = max(preserved_lines)
        
#         print(f'Sign use in preserved lines, manuscript:')
#         print('\tNumber of preserved lines in this manuscript:', len(preserved_lines))
#         print(f"\tMean average line length: {average_line_len}")
#         print(f"\tMedian average line length: {median_line_len}")
#         print(f"\tShortest line length: {shortest_line_len}")
#         print(f"\tLongest line length: {longest_line_len}")
#         print(preserved_lines)
        
#     return preserved_lines, preserved_lines_contents

""" WORD ANALYSIS -------------------------------------------------------------------------------------------------------------------- """
def normalise_line_text_for_word_analysis(input_line_data):
    final_line = ''
    
    for element in input_line_data:
        if element['type'] == 'manuscript designation':
            continue
        elif element['type'] == 'post/determinative':
            final_line += f'*{element['text'].upper()}*'
        elif element['type'] == 'ideo/logographic':
            final_line += element['text'].upper()
        else:
            final_line += element['text']
            
    return final_line


def merge_and_sum_dicts(*dicts):
    """ Function for merging dicts, used for combining different statistical dictionaries. """
    merged_dict = defaultdict(int)
    for d in dicts:
        for key, value in d.items():
            merged_dict[key] += value
    return dict(merged_dict)


def tag_line_with_info(input_line_text):
    """ Function used for tagging line text so it can be analysed as single words with information on their state of preservation. """
    input_line_text = input_line_text.replace('[…]', '')
    input_line_text = input_line_text.replace('…', '')
    input_line_text = input_line_text.replace('[...]', '')
    input_line_text = input_line_text.replace('...', '')
    tagged_line = []

    current_sign = ''
    tag_char = '°'
    for char in input_line_text:
        if char in ['[', '⸢', '<', '(']:
            if current_sign == '':
                tag_char = char
                continue
            else:
                tagged_line.append(f'{tag_char}:{current_sign}')
                current_sign = ''
                tag_char = char
        elif char in [']', '⸣', '>', ')']:
            if current_sign == '':
                tag_char = '°'
                continue
            else:
                tagged_line.append(f'{tag_char}:{current_sign}')
                current_sign = ''
                tag_char = '°'
        elif char.isalnum() or char == '/' or char == '*' or char == '.' or char == '?' or char == '!' or char == '+':
            current_sign += char
        elif char == ' ':
            if current_sign == '':
                continue
            else:
                tagged_line.append(f'{tag_char}:{current_sign}')
                current_sign = ''
        elif char == '-':
            tagged_line.append(f'{tag_char}:{current_sign}-')
            current_sign = ''
        else:
            print(char)
            print('something is going on...')
            
    if current_sign != '':
        tagged_line.append(f'{tag_char}:{current_sign}')

    return tagged_line


def get_words_from_tagged_line(tagged_line:list, double_readings_select=1):
    
    reconstructed_words_in_line = defaultdict(int)
    partially_reconstructed_words_in_line = defaultdict(int)
    preserved_words_in_line = defaultdict(int)
    
    current_word = ''
    current_word_state = ''
    connect_next = False
    for i, element in enumerate(tagged_line):
        element_state_tag = element.split(':')[0]
        sign_in_element = element.split(':')[1]
        if '/' in sign_in_element:
            if not double_readings_select:
                continue
            else:
                sign_in_element = sign_in_element.split('/')[double_readings_select]
        
        if connect_next:
            current_word += sign_in_element
            current_word_state += element_state_tag
        elif sign_in_element.startswith('-'):
            current_word += sign_in_element
            current_word_state += element_state_tag
        else:
            """ When the element does not connect either way, the current word must be recorded and new started. """
            tags = set(list(current_word_state))
            if tags == {'°'}:
                preserved_words_in_line[current_word] += 1
            elif '⸢' in tags:
                partially_reconstructed_words_in_line[current_word] += 1
            elif '[' in tags or '<' in tags or '(' in tags:
                if '°' in tags:
                    partially_reconstructed_words_in_line[current_word] += 1
                else:
                    reconstructed_words_in_line[current_word] += 1
            else:
                pass
                
            current_word = sign_in_element
            current_word_state = element_state_tag
                
            
        if sign_in_element.endswith('-'):
            connect_next = True
        else:
            connect_next = False
            
    if current_word != '':
        """ Add the last word/element after the line has ended. """
        tags = set(list(current_word_state))
        if tags == {'°'}:
            preserved_words_in_line[current_word] += 1
        elif '⸢' in tags:
            partially_reconstructed_words_in_line[current_word] += 1
        elif '[' in tags or '<' in tags or '(' in tags:
            if '°' in tags:
                partially_reconstructed_words_in_line[current_word] += 1
            else:
                reconstructed_words_in_line[current_word] += 1
        else:
            print('error? in adding the last word in line', tagged_line, current_word, tags)
            
    """ Now remove empty words/elements and X elements """
    for non_word in ['', 'x', '(x)']:
        try:
            del partially_reconstructed_words_in_line[non_word]
            #print(non_word, 'deleted')
        except KeyError:
            continue
    
    for non_word in ['', 'x', '(x)']:
        try:
            del reconstructed_words_in_line[non_word]
            #print(non_word, 'deleted')
        except KeyError:
            continue
        
    for non_word in ['', 'x', '(x)']:    
        try:
            del preserved_words_in_line[non_word]
            #print(non_word, 'deleted')
        except KeyError:
            continue

    # print('partially preserved words:', partially_reconstructed_words_in_line)
    # print('preserved words:', preserved_words_in_line)
    # print('reconstructed words:', reconstructed_words_in_line)
    
    return partially_reconstructed_words_in_line, preserved_words_in_line, reconstructed_words_in_line


def analyse_words_used(input_data:dict, double_readings_select=1, print_results=False):
    """
    This function provides analysis of words used in a given dataset (prepared with function extract_data_from_composition_document(input_document))

    Args:
        input_data (dict): manuscript object created wit function extract_data_from_composition_document(input_document).
        double_readings_select (int or bool/None): if False/None, signs that have two possible readings will be read as both (e.g., 'ze/zi'), if 0, the first will be selected, it 1, the second will be selected.
        print_results (bool): if True, the results will be printed.
    """
    
    reconstructed_words_used_in_dataset = defaultdict(int)
    partially_reconstructed_words_used_in_dataset = defaultdict(int)
    preserved_words_used_in_dataset = defaultdict(int)
    
    for section in input_data:
        for line in input_data[section]['cuneiform_data']:
            if 'note' in line:
                continue
            else:
                line_data = input_data[section]['cuneiform_data'][line]
                normalised_line = normalise_line_text_for_word_analysis(input_line_data=line_data)
                
                tagged_line = tag_line_with_info(normalised_line)
                
                partially_reconstructed_words_in_line, preserved_words_in_line, reconstructed_words_in_line = get_words_from_tagged_line(tagged_line=tagged_line, double_readings_select=double_readings_select)
                
                for word in reconstructed_words_in_line:
                    reconstructed_words_used_in_dataset[word] += reconstructed_words_in_line[word]
                
                for word in partially_reconstructed_words_in_line:
                    partially_reconstructed_words_used_in_dataset[word] += partially_reconstructed_words_in_line[word]
                    
                for word in preserved_words_in_line:
                    preserved_words_used_in_dataset[word] += preserved_words_in_line[word]
                
    full_words_used_in_dataset = merge_and_sum_dicts(reconstructed_words_used_in_dataset, partially_reconstructed_words_used_in_dataset, preserved_words_used_in_dataset)
    
    reconstructed_words_used_in_dataset = dict(sorted(reconstructed_words_used_in_dataset.items(), key=lambda item: item[1], reverse=True))
    partially_reconstructed_words_used_in_dataset = dict(sorted(partially_reconstructed_words_used_in_dataset.items(), key=lambda item: item[1], reverse=True))
    preserved_words_used_in_dataset = dict(sorted(preserved_words_used_in_dataset.items(), key=lambda item: item[1], reverse=True))
    full_words_used_in_dataset = dict(sorted(full_words_used_in_dataset.items(), key=lambda item: item[1], reverse=True))
                    
    if print_results:
        print('Number of all words/elements used in dataset:', len(full_words_used_in_dataset))
        print('Number of fully reconstructed words/elements used in dataset:', len(reconstructed_words_used_in_dataset))
        print('Number of partially reconstructed words/elements used in dataset:', len(partially_reconstructed_words_used_in_dataset))
        print('Number of fully preserved words/elements used in dataset:', len(preserved_words_used_in_dataset))
        
        print('Top 10 from all words/elements:', dict(islice(full_words_used_in_dataset.items(), 10)))
        print('Top 10 fully reconstructed words/elements:', dict(islice(reconstructed_words_used_in_dataset.items(), 10)))
        print('Top 10 partially reconstructed words/elements:', dict(islice(partially_reconstructed_words_used_in_dataset.items(), 10)))
        print('Top 10 fully preserved words/elements used in dataset:', dict(islice(preserved_words_used_in_dataset.items(), 10)))
                
    return reconstructed_words_used_in_dataset, partially_reconstructed_words_used_in_dataset, preserved_words_used_in_dataset, full_words_used_in_dataset


def word_sort_key(item):
    return item[0].lstrip('*').lower()


def get_table_of_words(reconstructed_words_used_in_dataset, partially_reconstructed_words_used_in_dataset, preserved_words_used_in_dataset, full_words_used_in_dataset):
    """ This functions serves to return dictionary for frontend table that includes attestations. """
    result_table_data = {}
    
    for word_form in full_words_used_in_dataset:
        try:
            preserved_count = preserved_words_used_in_dataset[word_form]
        except KeyError:
            preserved_count = 0
            
        try:
            partial_count = partially_reconstructed_words_used_in_dataset[word_form]
        except KeyError:
            partial_count = 0
            
        try:
            reconstructed_count = reconstructed_words_used_in_dataset[word_form]
        except KeyError:
            reconstructed_count = 0
            
        result_table_data[word_form] = {'preserved': preserved_count, 'partially preserved': partial_count, 'reconstructed': reconstructed_count}
        
        result_table_data = dict(sorted(result_table_data.items(), key=word_sort_key))
    
    return result_table_data
        

""" GLOSSARY CREATION -------------------------------------------------------------------------------------------------------------------- """
def normalise_line_text_for_forms_analysis(input_line_data):
    final_line = ''
    
    for element in input_line_data:
        if element['type'] == 'manuscript designation':
            continue
        elif element['type'] == 'post/determinative':
            final_line += f'*{element['text'].upper()}*'
        elif element['type'] == 'ideo/logographic':
            final_line += element['text'].upper()
        else:
            final_line += element['text']
            
    return final_line


def element_evaluation(element:str):
    """ This function recognises if the word/element has potential to be a form attestation or not. """
    score = 0
    for char in element:
        if char in ['', 'x', ' ', '.', '-', '[', ']', '⸢', '⸣', '<', '>', '*', '(', ')', '…', '...']:
            continue
        else:
            score += 1
    
    if score == 0:
        return False
    else:
        return element
    
    
ignore_chars = ['[', ']', '⸢', '⸣', '<', '>', '(', ')', '*']
ignore_pattern = re.compile(r'^[\[\]⸢⸣<>\(\)\*]+')

def clean_key(key):
    return ignore_pattern.sub('', key).lower()

def sort_dict_with_ignore_chars(input_dict:dict):
    sorted_dict = dict(sorted(input_dict.items(), key=lambda item: clean_key(item[0])))
    return sorted_dict


def check_non_space_word_boundaries(element:str):
    elements_in_element = []
    
    current_element = ''
    connect_over_breaks = False
    for i, char in enumerate(element):
        if char.isalnum() or char == '?' or char == '!' or char == '*' or char == '.' or char == '+' or char == '/':
            current_element += char
            connect_over_breaks = False
        elif char == '-' and element[i-1] in ['[', ']', '⸢', '⸣', '<', '>', '(', ')']:
            current_element += char
            connect_over_breaks = False
        elif char == '-':
            current_element += char
            connect_over_breaks = True
        elif char in ['[', ']', '⸢', '⸣', '<', '>', '(', ')'] and connect_over_breaks:
            current_element += char
        else:
            try:
                if element[i+1] == '-' or element[i+1] == '.':
                    current_element += char
                elif element [i+2] == '-' or element [i+2] == '.':
                    current_element += char
                else:                    
                    if char in [']', '⸣', '>', ')']:
                        current_element += char
                        if element_evaluation(current_element):
                            elements_in_element.append(current_element)
                        current_element = ''
                    else:
                        if element_evaluation(current_element):
                            elements_in_element.append(current_element)
                        current_element = char
            except IndexError:
                if char in [']', '⸣', '>', ')']:
                    current_element += char
                    if element_evaluation(current_element):
                        elements_in_element.append(current_element)
                    current_element = ''
                else:
                    if element_evaluation(current_element):
                        elements_in_element.append(current_element)
                    current_element = char

    
    """ Add the last element. """
    if element_evaluation(current_element):
        elements_in_element.append(current_element)
        
    return elements_in_element


def extract_word_from_normalised_line(input_line_text:str):
    """ This function extracts eords/elements from a given line. On each word, there is an indication of reconstruction tags. """
    final_words_attestations = []
    possible_words = input_line_text.split(' ')
    
    reconstruction_open = False
    partial_reconstruction_open = False
    for word in possible_words:
        if element_evaluation(word):
            words = check_non_space_word_boundaries(word)
            for w in words:
                if reconstruction_open and partial_reconstruction_open:
                    print('ERROR, both reconstruction and partial reconstruction cannot be open!!', w, input_line_text)
                elif reconstruction_open:
                    w = '['+w
                elif partial_reconstruction_open:
                    w = '⸢'+w
                else:
                    pass
                    
                for char in w:
                    if char == '[':
                        reconstruction_open = True
                    elif char == ']':
                        reconstruction_open = False
                    elif char == '⸢':
                        partial_reconstruction_open = True
                    elif char == '⸣':
                        partial_reconstruction_open = False
                    else:
                        pass
                
                if reconstruction_open and partial_reconstruction_open:
                    print('ERROR, both reconstruction and partial reconstruction cannot be open!!', w, input_line_text)
                elif reconstruction_open:
                    w = w+']'
                elif partial_reconstruction_open:
                    w = w+'⸣'
                else:
                    pass
                
                final_words_attestations.append(w)

        else:
            continue
    
    return final_words_attestations


def extract_attested_forms_from_manuscript(input_data):
    """
    This function extracts data about attested forms of words/elements from a given manuscript. Post/Determinatives are recognised as part of the whole word. Reconstructions, additions, etc. are preserved in the attestation form. The data are then sorted alphabetically.

    Args:
        input_data (dict): manuscript object created wit function extract_data_from_composition_document(input_document).
        csv_out_path (str): path to the CSV file where the data should be stored. Note that the file will be overwritten!!
    """
    
    forms_on_lines = defaultdict(list)
    
    for section, section_data in input_data.items():
        print('... processing section', section, '...')
        section_cuneiform_data = section_data['cuneiform_data']
        for line_designation, line_data in section_cuneiform_data.items():
            if 'note' in line_designation:
                continue
            else:
                line_text = normalise_line_text_for_forms_analysis(line_data)
                
                line_words = extract_word_from_normalised_line(input_line_text=line_text)
                #print(line_words)
                
                for form in line_words:
                    forms_on_lines[form].append(line_designation)
                
    forms_on_lines_sorted = sort_dict_with_ignore_chars(input_dict=forms_on_lines)
                    
    dict_for_df = {}
    for key_form, line_attestations in forms_on_lines_sorted.items():
        lines_for_df = ''
        for line in line_attestations:
            lines_for_df += f'\n{line}'
        lines_for_df = lines_for_df[1:]
        
        entry = {'CDA form': '', 'CDA meaning': '', 'used meaning': '', 'attestation': lines_for_df}
        
        dict_for_df[key_form] = entry
    
    return dict_for_df

""" ORACC PREPROCESSING -------------------------------------------------------------------------------------------------------------------- """
def to_subscript(number):
    subscript_map = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', 'x': 'ₓ'
    }
    
    try:
        int(number)
        return ''.join(subscript_map[digit] for digit in str(number))
    except ValueError:
        return 'ERROR'

def normalise_line_for_oracc(input_line_data: list):
    oracc_norm_line = ''
    error = False
    
    for element in input_line_data:
        if element['type'] == 'manuscript designation':
            continue
        elif element['type'] == 'post/determinative':
            oracc_norm_line += '{'+element['text'].lower()+'}'
        elif element['type'] == 'sign number':
            sign_num_in_sub = to_subscript(element['text'])
            if sign_num_in_sub == 'ERROR':
                error = True
            oracc_norm_line += sign_num_in_sub
        else:
            oracc_norm_line += element['text']
    
    return oracc_norm_line, error


def check_errors_in_line_parsing(input_norm_line: str):
    input_norm_line = input_norm_line.replace('<<', '%')
    input_norm_line = input_norm_line.replace('>>', '@')
    
    reconstruction_open = False
    partialreconstruction_open = False
    bracket_open = False
    edit_open = False
    erase_open = False
    
    for sign in input_norm_line:
        if sign == '[':
            if partialreconstruction_open or reconstruction_open:
                return True
            reconstruction_open = True            
        elif sign == ']':
            if not reconstruction_open:
                return True
            reconstruction_open = False
        elif sign == '⸢':
            if reconstruction_open or partialreconstruction_open:
                return True
            partialreconstruction_open = True            
        elif sign == '⸣':
            if not partialreconstruction_open:
                return True
            partialreconstruction_open = False
        elif sign == '(':
            if bracket_open:
                return True
            bracket_open = True
        elif sign == ')':
            if not bracket_open:
                return True
            bracket_open = False
        elif sign == '<':
            if edit_open:
                return True
            edit_open = True
        elif sign == '>':
            if not edit_open:
                return True
            edit_open = False
        elif sign == '%':
            if erase_open:
                return True
            erase_open = True
        elif sign == '@':
            if not erase_open:
                return True
            erase_open = False
            
    return False


def oraccise_line(input_norm_line: str):
    final_oracc_line = ''
    partial = False
    after_space = False
    
    for sign in input_norm_line:
        if sign == '⸢':
            partial = True
        elif sign == '⸣':
            partial = False
        elif sign == ' ' and partial:
            final_oracc_line += '# '
        elif sign == '-' and partial:
            final_oracc_line += '#-'
        elif sign == '{' and partial and not after_space:
            final_oracc_line += '#{'
        elif sign == '}' and partial:
            final_oracc_line += '#}'
        else:
            final_oracc_line += sign
            
        if sign == ' ':
            after_space = True
        else:
            after_space = False
            
    if partial:
        final_oracc_line += '#'
    
    return final_oracc_line


def prepare_lem_line(input_orracised_line:str):
    elements = input_orracised_line.split(' ')
    lem_line = '#lem:'
    for elem in elements:
        lem_line += ' u;'
    
    return lem_line[:-1]


def parse_line_id(line_id:str, rec_vers=True, cols=True, lines=True):
    """ This function parse line id according to the data it contains. """
    if rec_vers and cols and lines:
        try:
            line_id_elems = line_id.split(' ')
            rec_ver = line_id_elems[0]
            col = line_id_elems[2].lower()
            line = line_id_elems[3]
        except:
            return 'Error in parsing line designation', '-', '-'
    
    elif not rec_vers and cols and lines:
        try:
            line_id_elems = line_id.split(' ')
            rec_ver = ''
            col = line_id_elems[1].lower()
            line = line_id_elems[2]
        except:
            return 'Error in parsing line designation', '-', '-'
        
    elif not rec_vers and not cols and lines:
        try:
            rec_ver = ''
            col = ''
            line = line_id
        except:
            return 'Error in parsing line designation', '-', '-'
        
    elif rec_vers and not cols and lines:
        try:
            line_id_elems = line_id.split(' ')
            rec_ver = line_id_elems[0]
            col = ''
            line = line_id_elems[1]
        except:
            return 'Error in parsing line designation', '-', '-'
    
    else:
        return 'Error in parsing line designation', '-', '-'
    
    return rec_ver, col, line


def roman_to_arabic(roman):
    roman_values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    
    if not all(char in roman_values for char in roman.upper()):
        return roman
    
    arabic = 0
    prev_value = 0
    
    for char in reversed(roman.upper()):
        current_value = roman_values[char]
        if current_value >= prev_value:
            arabic += current_value
        else:
            arabic -= current_value
        prev_value = current_value
    
    return arabic


def parse_section(section_id:str, rec_vers=True, cols=True):
    """ This function parses the section id (taken from the heading in DOCX document) so it can be used in the ORACC manuscript designation. """
    if rec_vers and cols:
        try:
            section_id_elems = section_id.split(' ')
            rec_ver = section_id_elems[0].lower()
            col_num = section_id_elems[2].lower()
        except:
            return 'Error in parsing line designation', '-',
        
    elif not rec_vers and cols:
        try:
            section_id_elems = section_id.split(' ')
            rec_ver = ''
            col_num = section_id_elems[1].lower()
        except:
            return 'Error in parsing line designation', '-',
        
    elif rec_vers and not cols:
        try:
            rec_ver = section_id.lower()
            col_num = ''
        except:
            return 'Error in parsing line designation', '-',
        
    if rec_ver:
        if 'obv' in rec_ver or 'rec' in rec_ver or rec_ver == 'vs.':
            rec_ver = 'obverse'
        elif 'rev' in rec_ver or 'ver' in rec_ver or rec_ver == 'rs.':
            rec_ver = 'reverse'
            
    if col_num:
        col_num = f'column {roman_to_arabic(col_num)}'
        
    return rec_ver, col_num


def oraccise_document(input_document_data: dict, rec_vers=True, cols=True, lines=True):
    """ This function transforms data from processed document into form that corresponds with the ORACC ATF formatting. """
    
    error_report = {}
    oracc_doc = 'MANUSCRIPT = ADD IDs AND DESIGNATIONS\n\n#project: ADD PROJECT NAME\n#atf: use unicode\n#atf: lang ADD LANG DESIGNATION (e.g., akk-x-oldbab)\n#atf: use math\n#atf: use legacy\n\n@tablet'
    current_o_r = None
    
    # NOTE: first, process the cuneiform input
    for section in input_document_data:
        rec_ver, col_num = parse_section(section, rec_vers=rec_vers, cols=cols)
        if current_o_r == None:
            if rec_ver:
                oracc_doc += f'\n@{rec_ver}'
                current_o_r = rec_ver
            else:
                pass
        else:
            if rec_ver == current_o_r:
                pass
            else:
                oracc_doc += f'\n@{rec_ver}'
                current_o_r = rec_ver
            
        if col_num:
            oracc_doc += f'\n@{col_num}'
        else:
            pass
        
        section_cuneiform_data = input_document_data[section]['cuneiform_data']
        for line_id, line_data in section_cuneiform_data.items():
            if 'note' in line_id:
                oracc_doc += f'\n\n$ {line_data}\n'
                continue
            else:
                line_num = line_id.split(' ')[-1]
                norm_line_text, norm_line_error = normalise_line_for_oracc(line_data)
                if check_errors_in_line_parsing(norm_line_text):
                    error_report[line_id] = 'PARSE error in parsing this line, check the line in the raw document.'
                if norm_line_error:
                    error_report[line_id] = 'SIGN error in sign number designation this line, check the line in the raw document.'
                
                oraccised_line = oraccise_line(norm_line_text)
                # add cuneiform line data
                oracc_doc += f'\n{line_num}. {oraccised_line}'
                # add line for lemmatization
                lem_line = prepare_lem_line(oraccised_line)
                oracc_doc += '\n'+lem_line+'\n'    
    
    # NOTE: second, process the translation input
    oracc_doc += '\n\n@translation labeled en project'
    for section in input_document_data:
        section_translation_data = input_document_data[section]['translation_data']
        for line_id, line_data in section_translation_data.items():
            if 'note' in line_id:
                oracc_doc += f'\n\n$ {line_data}\n'
                continue
            else:    
                rec_ver, col, line = parse_line_id(line_id, rec_vers=rec_vers, cols=cols)
                if rec_ver:
                    rec_ver = rec_ver[0]
                
                trsl_line_des = f'({rec_ver} {col} {line})'
                trsl_line_des = trsl_line_des.replace('  ', ' ')
                trsl_line_des = trsl_line_des.replace('( ', '(')
                trsl_line_des = trsl_line_des.replace(' )', ')')
                
                oracc_doc += f'\n@{trsl_line_des} {line_data}\n'
    
    print(oracc_doc)
    
    return oracc_doc, error_report
    

""" MANUSCRIPT COMPARISON -------------------------------------------------------------------------------------------------------------------- """
# TODO - So far, the script is not set for multiple manuscript comparison.
def overlap_of_signs_in_manuscripts(signs_man_1:dict, signs_man_2:dict):
    """ This function compares the sign usage in two manuscripts. """
    unique_signs_in_1 = {}
    unique_signs_in_2 = {}
    overlap = {}
    
    for sign_1 in signs_man_1:
        if sign_1 in signs_man_2:
            overlap[sign_1] = (signs_man_1[sign_1], signs_man_2[sign_1])
        else:
            unique_signs_in_1[sign_1] = signs_man_1[sign_1]
            
    for sign_2 in signs_man_2:
        if sign_2 in overlap:
            continue
        else:
            unique_signs_in_2[sign_2] = signs_man_2[sign_2]
            
    print('Number of unique signs in manuscript no. 1:', len(unique_signs_in_1), 'of original', len(signs_man_1))
    print('Number of unique signs in manuscript no. 2:', len(unique_signs_in_2), 'of original', len(signs_man_2))
    
    print('Overlap has been found in', len(overlap), 'signs')
    
    sorted_1 = dict(sorted(overlap.items(), key=lambda item: item[1][0], reverse=True))
    sorted_2 = dict(sorted(overlap.items(), key=lambda item: item[1][1], reverse=True))
    
    print('Top 10 overlapped signs (according to no. 1):', dict(islice(sorted_1.items(), 10)))
    print('Top 10 overlapped signs (according to no. 2):', dict(islice(sorted_2.items(), 10)))
    
    return unique_signs_in_1, unique_signs_in_2, overlap