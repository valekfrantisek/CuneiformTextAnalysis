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


""" SIGN ANALYSIS """
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
        for line in input_data[section]:
            if 'note' in line:
                continue
            else:
                line_data = input_data[section][line]
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
def get_signs_from_preserved_line(line_text:str):
    """ Remove longer parts of missing signs and unrecognised sings. """
    if '...' in line_text or '…' in line_text:
        return False
    
    else:
        delimiters = ' -.*[]⸢⸣<>()'
        regex_pattern = f"[{re.escape(delimiters)}]"
        signs_in_line = re.split(regex_pattern, line_text)
        
        signs_in_line = [s for s in signs_in_line if s]
                
        return signs_in_line


def get_line_length_in_manuscript(input_manuscript:dict):
    preserved_lines = []
    preserved_lines_contents = []
    for col, col_text in input_manuscript.items():
        for line, line_data  in col_text.items():
            if 'note' in line:
                continue
            else:
                normalised_line = normalise_line_text_for_sign_analysis(input_line_data=line_data)
                
            line_signs_if_preserved = get_signs_from_preserved_line(line_text=normalised_line)
            if line_signs_if_preserved:
                preserved_lines.append(len(line_signs_if_preserved))
                preserved_lines_contents.append(normalised_line)
            else:
                continue
    
    if preserved_lines == []:
        print('No preserved lines in this manuscript!')
    else:
        average_line_len = statistics.mean(preserved_lines)
        median_line_len = statistics.median(preserved_lines)
        shortest_line_len = min(preserved_lines)
        longest_line_len = max(preserved_lines)
        
        print(f'Sign use in preserved lines, manuscript:')
        print('\tNumber of preserved lines in this manuscript:', len(preserved_lines))
        print(f"\tMean average line length: {average_line_len}")
        print(f"\tMedian average line length: {median_line_len}")
        print(f"\tShortest line length: {shortest_line_len}")
        print(f"\tLongest line length: {longest_line_len}")
        print(preserved_lines)
        
    return preserved_lines, preserved_lines_contents

""" WORD ANALYSIS """

""" GLOSSARY CREATION """

""" ORACC PREPROCESSING """

""" MANUSCRIPT COMPARISON """
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