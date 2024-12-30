# Cuneiform Text Analysis

This repository contains scripts for online app Cuneiform Text Analyser. The scripts provided here are built to run this app on your own computer.

The project is also served at [https://dh-tools.eu/CTA/](https://dh-tools.eu/CTA/).

## Current Version
version: 1.0.1

publised: 30 December 2024

license: [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)

## Available Functions
### Cuneiform text from MS Word analysis
The scriprt enables analysis of transcribed cuneiform texts in Word, structured in tables. So far, it is able to analyse text where transcribed text and translation are structured in lines or in columns. It is also able to analyse cuneiform text without translation.

For examples of input documents, see [docx examples](https://github.com/valekfrantisek/CuneiformTextAnalysis/tree/main/frontend/examples).

The functions currently enable to:
1) show the text in the app in tables
2) analyse signes used in the input docement, counting separately signs that are preserved, partially preserved, reconstructed by the editor, or otherwise added to the text.
3) analysed word forms used in the input docement, counting separately forms that are preserved, partially preserved, reconstructed by the editor
4) prepare glossary, i.e., collecting attestations of word forms.

### Transformation of MS Word files to ATF for ORACC
The script also serves to pretere ATF files for ORACC ([Open Richly Annotated Cuneiform Corpus](https://oracc.museum.upenn.edu/)) based on the input document. This should help with the transformation of Word documents into enriched digital collection.

## Work in Progress
Additional tools and functionalities are being prepared. If you have any suggestions, write to [frantisek.valek@upce.cz](mailto:frantisek.valek@upce.cz)

- Different use of break indications (e.g., [šum-m]a = [šum]⸢-ma⸣)
- Analyse CSV input
- Analyse XLSX input
- Analyse Word non-tabular input
- ORACC intertextual analysis
