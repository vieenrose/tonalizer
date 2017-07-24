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

* Unix-like Operation System (Linux, MacOS)
```
sudo pip install python-Levenshtein python-crfsuite nltk
```


## General Functions
- [ ] Undiacritize a UTF-8 raw text (.txt)

- [x] Generate a model file from a diacritized text and evaluate accuracy

```
python tonalizer.py [input text filename] -l [model filename]
```


- [ ] Use a model to recover diacrtize of a new text

## Experiment Results (Preliminary)**

|          Ressource | File Size | File Name | Language | Diacritization / Tonalization Accuracy |
|:------------------:|----------:|:----------|:--------:|---------------------------------------:|
| T. Zerrouki et al. |           |           |          |                                        |

**Reference**

* T. Zerrouki, A. Balla, Tashkeela: Novel corpus of Arabic vocalized texts, data for auto-diacritization systems, Data in Brief (2017) <a href="https://sourceforge.net/projects/tashkeela/" target="_blank">link</a>
