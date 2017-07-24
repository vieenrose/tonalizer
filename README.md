# Tonalizer - CRF-based Tone Reconstitution Tool

* Introduction

In many languages such as Bambara or Arabic, tone markers (diacritics) may be written but are actually often omitted. Lack of tone markers contribute to ambiguities and subsequent difficulties when reading texts. To circumvent this problem, tonalization may be used, as a word sense disambiguation task, relying on context to add diacritics that partially disambiguate words as well as senses. 

* Objective 

Tonalizer we propose here models tonalizaion of a tonalized text in UTF-8, and generate a model file. With the model file leant, tonalizer can performs reconstitue tone markers of a new raw text without diacritics. 
	
* General Functions
- [ ] Undiacritize a UTF-8 raw text (.txt)
- [x] Generate a model file from a diacritized text and evaluate accuracy
- [ ] Use a model to recover diacrtize of a new text

* Experiment Results (Preliminary)

|     Ressource | File Size | File Name | Language | Diacritization / Tonalization Accuracy |
|:-------------:|----------:|:----------|:--------:|---------------------------------------:|
| Tashkeela [1] |           |           |          |                                        |

[1] T. Zerrouki, A. Balla, Tashkeela: Novel corpus of Arabic vocalized texts, data for auto-diacritization systems, Data in Brief (2017)

