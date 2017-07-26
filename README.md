# Tonalizer - CRF-based Tone Reconstitution Tool

## Introduction

In many languages such as Bambara or Arabic, tone markers (diacritics) may be written but are actually often omitted. Lack of tone markers contribute to ambiguities and subsequent difficulties when reading texts. To circumvent this problem, tonalization may be used, as a word sense disambiguation task, relying on context to add diacritics that partially disambiguate words as well as senses.


## Objective

Tonalizer we propose here models tonalizaion of a tonalized text in UTF-8, and generate a model file. With the model file leant, tonalizer can performs reconstitue tone markers of a new raw text without diacritics. 
	
## System Requirements
* python >= 2.4
* python-Levenshtein
* python-crfsuite
* nltk

## Installation

* Unix-like Operating System (Linux, MacOS)
```
sudo pip install python-Levenshtein python-crfsuite nltk
```


## General Functions
### Undiacritizing
- [x] Undiacritize a UTF-8 stream received by stdin and show result to stdout
```
PROGRAM | python tonalizer.py -u
```
- [x] Undiacritize a UTF-8 raw text (.txt) and show result to stdout
```
python tonalizer.py -i infile -u
```
- [x] Undiacritize a UTF-8 raw text (.txt) and save result to file
```
python tonalizer.py -i infile -u -o outfile
```

### Training
- [x] Generate a model file from a diacritized text, then store it in a file and show accuracy to screen

```
python tonalizer.py -i infile -l model -s report.csv
```
- [x] Generate a model file from a UTF-8 stream received by stdin, then store it in a file and show accuracy to screen
```
PROGRAM | python tonalizer.py -l model -s report.csv
```

### Diacritizing
- [x] Use a model to recover diacrtize of a UTF-8 stream, then outputs to screen
```
PROGRAM | python tonalizer.py -d model 
```
- [x] Use a model to recover diacrtize of a new text, then outputs to a file
```
python tonalizer.py -i infile -d model -o outfile
```
- [x] Use a model to recover diacrtize of a UTF-8 stream, then outputs to a file
```
PROGRAM | python tonalizer.py -d model -o outfile 
```



## Experiment Results (Preliminary)

|          Ressource | File Size | File Name                      | Language | Accuracy | Train/Test Ratio |
|:------------------:|----------:|:-------------------------------|:--------:|---------:|:----------------:|
| Project Gutenberg. |   696 KB  | pg17489.txt                    | French   | 0.975    | 90 : 10          |
| T. Zerrouki et al. |           | معالم القربة في طلب الحسبة.txt | Arabic   |          |                  |

**Reference**

* Project Gutenberg. (n.d.). Retrieved July 26, 2017, from www.gutenberg.org. <a href="https://www.gutenberg.org/" target="_blank">link</a>
* T. Zerrouki, A. Balla, Tashkeela: Novel corpus of Arabic vocalized texts, data for auto-diacritization systems, Data in Brief (2017) <a href="https://sourceforge.net/projects/tashkeela/" target="_blank">link</a>

