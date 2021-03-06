#! /usr/bin/env python
# coding=utf-8

import sys, math, unicodedata
from collections import Counter, defaultdict
import Levenshtein
import re
import itertools
import csv
import codecs

# Installation of prerequisites
# sudo pip install python-Levenshtein

# Constant lists
code_seperator = u'_'
mode_indicators = u'+-'
mode_names   = [u"insert",u"delete"]

def code_dispatcher(code, sel_en) :

	lst = [""]

	if not code : return lst
	if not is_a_good_code(code) : print "(dispatcher) input code incorrect !" ; print code ; exit()
	#if code[-1] == code_seperator : code = code[: -1]
	# code_segments = code.split(code_seperator)
	code_segments = split2(code,code_seperator)

	# Filtering
	def indexing(op) :
		m,p,c = op
		return 2 * int(p) + mode_indicators.index(m)

	ops = [code_segments[i : i + 3] for i in range(0, len(code_segments), 3)]

	if sel_en :
		ops = sorted(ops, key=lambda op : indexing(op))
		ops2 = list()
		i_pre = -1
		for op in ops :
			i = indexing(op)
			if i > i_pre :
				ops2.append(op)
			i_pre = i
	else :
		ops2 = ops

	for op in ops2 :
		m,p,c = op
		lst[0] += \
			u"{}{}{}{}{}{}".format(m, code_seperator, p, code_seperator, c, code_seperator)

	lst2 = list()
	for element in lst :
		try :
			if element[-1] == code_seperator or element[-1] == code_seperator.decode('utf-8') :
				lst2.append(element[:-1])
			else :
				lst2.append(element)
		except :
			lst2.append(element)

	for code in lst2 :
		if not is_a_good_code(code):
			print "(dispatcher) output code incorrect !"
			print code

	return lst2

def apply_filter_to_base_element(x, sel_en, show_approx_err = False) :

	if isinstance(x, tuple) :
		return (x[0], filter(x[0], x[1].decode("utf-8"), sel_en, show_approx_err).encode("utf-8"))
	else :
		return [apply_filter_to_base_element(element, sel_en, show_approx_err) for element in x]


def filter(token, tag, sel_en, show_approx_err = False) :

	subcodes = code_dispatcher(tag, sel_en)
	code2 = code_seperator.encode("utf-8").join([subcode for p, subcode in enumerate(subcodes)])
	ret = code_resort(code2)

	if ret != tag and show_approx_err  :
	# un prix d'approximation à payer :
	# notre décomposition de la CRF paye bien un prix : la perte de l'ordre des caractères (de types différents) à insérer sur
	# la même position par rapport qu token original, bien que ce soit rarissime d'insérer successivement un caractère non diacritique
	# et un diacritique à la même position sur un token, ça peut arriver, donc générer une erreur observable si nous dés-commentons
	# les lignes de code ci-dessous
	# par exemple,
	# tag_gold =         +_0_ɔ_+_0_̀_+_0_n_-_0_a
	# tag_reconstitued = +_0_ɔ_+_0_n_+_0_̀_-_0_a
	# pour rappel, cette erreur est comptée dans l'évaluation, et curieusement on n'a pas constaté de dégradation considérable
	# dans l'exactitude du résultat, ça peut s'expliquer par ce qu'une insertion successive est souvent dfficile à apprendre
	# en soi, (hypothèse à vérifier, donc), donc une perte d'ordre ne rend pas ce cas de figure plus catastrohpique quantitativement
		print "Case of modeling error inherent to decomposition hypothesis : \n", ret, tag

	return ret

def split2 (str_in, seperator) :

        buf = ''
        ret = []
        for c in str_in :
                if c != seperator :
                        buf += c
                else :
                        if buf :
                                ret.append(buf)
                                buf = ''
                        else :

                                buf += c
        if buf :
                ret.append(buf)
        return ret

def accuray2 (dataset1, dataset2, is_tone_mode = False) :
	cnt_sucess = 0
	cnt_fail = 0
	if not is_tone_mode :
		for sent1, sent2 in zip(dataset1, dataset2) :
			for token1, token2 in zip(sent1, sent2) :
				if token1 == token2 :
					cnt_sucess += 1
				else :
					cnt_fail += 1

	else :
		for sent1, sent2 in zip(dataset1, dataset2) :
			for token1, token2 in zip(sent1, sent2) :
				is_identical = True
				for syllabe1, syllabe2 in zip(token1, token2) :
					if syllabe1 != syllabe2 : is_identical = False ; break;
				if is_identical :
					cnt_sucess += 1
				else :
					cnt_fail += 1

	cnt_tot = cnt_sucess + cnt_fail
	if not cnt_tot : return 0.0
	else : return cnt_sucess / float(cnt_tot)

def get_sub_tone_code_of_sentence (sentence, sel_en) :
	labels = list()
	for i, token in enumerate(sentence) :
		label = list()
		for j, syllabe_code in enumerate(token) :
			syllabe, code = syllabe_code
			subcode = code_dispatcher(code.decode('utf-8'), sel_en)[0].encode('utf-8')
			label.append(subcode)
		labels.append(label)
	return labels

def accumulate_tone_code_of_dataset (dataset_acc, dataset) :
	for p, sent in enumerate(dataset_acc) :
		for i, token in enumerate(sent) :
			for j, syllabe_tag_acc in enumerate(token) :
				syllabe_acc, tag_acc = syllabe_tag_acc
				syllabe, tag = dataset[p][i][j]
				if tag_acc and tag :
					tag_acc += code_seperator.encode('utf-8') + tag
				else :
					tag_acc += tag
				dataset_acc[p][i][j] = \
					tuple([syllabe, code_resort(tag_acc.decode('utf-8')).encode('utf-8')])

	return dataset_acc

def reshape_tokens_as_sentnece(tokens, sentnece) :

	ret = list()
	n = 0
	for i, token in enumerate(sentnece) :
		tmp = list()
		for j, syllabe in enumerate(token) :
			tmp.append(tokens[n])
			n += 1
		ret.append(tmp)

	return ret

def make_tokens_from_sentence(sent, is_tone_mode = False) :
	if is_tone_mode :
		tokens = list()
		labels = list()
		for token in sent :
			tokens.append(unzip(token)[0])
			labels.append(unzip(token)[1])
	else :
		tokens = unzip(sent)[0]
		labels = unzip(sent)[1]

	return [tokens, labels]

def make_features_from_tokens(tokens, is_tone_mode = False) :
	if is_tone_mode :
		features_syllabe = list()
		for i, token in enumerate(tokens) :
			feature = list()
			for j, syllabe_code in enumerate(token) :
				feature.append(get_features_customised_tone(tokens, i, j))
			features_syllabe.append(feature)
		features = list(itertools.chain(*features_syllabe))
	else :
		features = list()
		for i in range(len(tokens)) :
			features.append(get_features_customised(tokens, i))
	return features

def inspector_tokens(gold_tokens, predicted_tokens) :
	for x,y in zip(gold_tokens, predicted_tokens) :
		try :
			if x[1] != y[1] :
				print x[0],":",x[1].decode('utf-8'),"->",y[1].decode('utf-8') # ,"(",len(x[1]), len(y[1]),")"
			else :
				print "*",x[0],":",x[1].decode('utf-8'),"->",y[1].decode('utf-8') # ,"(",len(x[1]), len(y[1]),")"
		except :
			print type(x[0]),":",type(x[1]),"->",type(y[1])

def unzip(input) :
	return [list(li) for li in zip(*input)]

def csv_export(filename, gold_set, test_set, is_tone_mode = False):

	if not is_tone_mode :
		csvfile = codecs.open(filename, 'wb')
		writer = csv.writer(csvfile)
		writer.writerow(["Token", "Golden", "Predicted", "Same"])
		for gold_sent, test_sent in zip(gold_set, test_set) :
			for gold_token, test_token in zip(gold_sent, test_sent) :
				token = gold_token[0]
				gold_code = gold_token[1]
				test_code = test_token[-1]
				# print token, gold_code, test_code
				sameCodes = (gold_code == test_code)

				if not repr(token.encode('utf-8')) :
					sameCodes = u''
				row = [\
				(token.encode('utf-8')), \
				gold_code, \
				test_code, \
				sameCodes]
				writer.writerow(row)
		csvfile.close()
	else :
		csvfile = codecs.open(filename, 'wb')
		writer = csv.writer(csvfile)
		writer.writerow(["Token", \
			"Golden Form","Predicted Form", \
			"Golden code", "Predicted code", "Same"])
		enc = encoder_tones()
		for gold_sent, test_sent in zip(gold_set, test_set) :
			for gold_token, test_token in zip(gold_sent, test_sent) :
				gold_code = ''
				test_code = ''
				gold_form = ''
				test_form = ''
				token = ''
				for gold_syllabe, test_syllabe in zip(gold_token, test_token) :
					token += gold_syllabe[0] + ' '
					if gold_syllabe[1] :
						gold_code += gold_syllabe[1] + ' '
					else :
						gold_code += 'NULL' + ' '
					if test_syllabe[1] :
						test_code += test_syllabe[1] + ' '
					else :
						test_code += 'NULL' + ' '
					gold_form += enc.differential_decode(gold_syllabe[0], gold_syllabe[1].decode('utf-8')) + ' '
					test_form += enc.differential_decode(gold_syllabe[0], test_syllabe[1].decode('utf-8')) + ' '
					sameCodes = (gold_code == test_code)
					sameForms = (gold_form == test_form)
				sameCodes = (gold_code == test_code)
				sameForms = (gold_form == test_form)
				if not repr(token.encode('utf-8')) :
					sameCodes = u''
				row = [\
				(token.encode('utf-8')), \
				repr(gold_form.encode('utf-8')), \
				repr(test_form.encode('utf-8')), \
				repr(gold_code, spaces=True), \
				repr(test_code, spaces=True), \
				sameCodes]
				writer.writerow(row)
		csvfile.close()

def sampling(allsents, p, ratio = 1) :
	train_set, eval_set = [], []
	for i, sent in enumerate(allsents[0 : : int(1/float(ratio))]) :
		p_approx = float(len(train_set) + 1) / float(len(eval_set) + len(train_set) + 1)
		if p_approx <= p :
			train_set.append(sent)
		else:
			eval_set.append(sent)
	return [train_set, eval_set]

def get_duration(t1_secs, t2_secs) :
	secs = abs(t1_secs - t2_secs)
	days = secs // 86400
	hours = secs // 3600 - days * 24
	minutes = secs // 60 - hours * 60 - days * 60 * 24
	secondes = int(secs) % 60
	return '{:>02.0f}:{:>02.0f}:{:>02.0f}:{:>02d}'.format(days, hours, minutes, secondes)

def is_a_good_code(code) :

	if not code : return True

	code2 = code

	# +_2__ is good, because -> + 2 _
	if code2[-1] == code_seperator.decode('utf-8') or code2[-1] == code_seperator :
		try :
			if code2[-1] != code2[-2] :
				return False
		except IndexError:
			return False

	# code3 = code2.split(code_seperator.decode('utf-8'))
	code3 = split2(code2,code_seperator.decode('utf-8'))
	if len(code3) % 3 != 0 :
		return False
	else :
		return True

def code_resort(code) :


	ret = []
	if not code : return code
	if not is_a_good_code(code) : print "(resort) input code incorrect !" ; exit()
	#if code[-1] == code_seperator : code = code[: -1]
	#code_segments = code.split(code_seperator)
	code_segments = split2(code,code_seperator)
	for i in range(0, len(code_segments), 3) :
		try :
			m, p, c = code_segments[i : i + 3]
		except :
			print code
			print code_segments;
			print "Bug 1 !"
			exit()

		ret.append(u"{}{}{}{}{}{}".format(m, code_seperator, p, code_seperator, c, code_seperator))

	ret = sorted(ret, key=lambda x : int(mode_indicators.index(split2(x, code_seperator)[0])) + 2 * int(split2(x, code_seperator)[1]))
	ret = ''.join(ret)
	if ret : ret = ret[:-1]

	if not is_a_good_code(ret) : print ("(resort) ouptut code incorrect !") ; exit()

	return ret

def get_features_customised(tokens, idx):

	feature_list = []

	if not tokens:
		return feature_list

	token = tokens[idx]

	# Capitalization
	if token[0].isupper():
		feature_list.append(u'CAPITALIZATION')

	# Number
	if re.search(r'\d', token) is not None:
		feature_list.append(u'IL_Y_A_UN_CHIFFRE')

	# Punctuation
	punc_cat = set([u"Pc", u"Pd", u"Ps", u"Pe", u"Pi", u"Pf", u"Po"])
	if all (unicodedata.category(x) in punc_cat for x in token):
		feature_list.append(u'PONCTUATION_PURE')

	# Syllabes précédent et suivant
	try :
		feature_list.append(u'TOKEN_PRECEDENT_' + token[idx - 1])
	except IndexError :
		pass

	try :
		feature_list.append(u'TOKEN_SUIVANT_' + token[idx + 1])
	except IndexError :
		pass

	feature_list.append(u'TOKEN_ACTUEL_' + (token))

	# Suffix & prefix up to length 3
	if len(token) > 1:
		feature_list.append(u'SUF_' + token[-1:])
		feature_list.append(u'PRE_' + token[:1])
	if len(token) > 2:
		feature_list.append(u'SUF_' + token[-2:])
		feature_list.append(u'PRE_' + token[:2])
	if len(token) > 3:
		feature_list.append(u'SUF_' + token[-3:])
		feature_list.append(u'PRE_' + token[:3])

	return feature_list

def get_features_customised_tone(tokens, i, j) :

	feature_list = []

	if not tokens:
		return feature_list

	try :
	 	syllabes = tokens[i]
		syllabe = syllabes[j]
	except IndexError :
		raise

	# Positions
	feature_list.append(u'SYLLABE_ID_POSITIF_' + str(j))
	feature_list.append(u'SYLLABE_ID_NEGATIF_' + str(len(syllabes) - j - 1))
	feature_list.append(u'TOKEN_ID_POSITIF_' + str(i))
	feature_list.append(u'TOKEN_ID_NEGATIF_' + str(len(tokens) - i - 1))

	# Châine de caractères au niveau du vocable actuel
	feature_list.append(u'SYLLABE_ACTUELLE_' + syllabe)
	feature_list.append(u'PREFIXE_ACTUEL_' + syllabes[0])
	feature_list.append(u'SUFFIXE_ACTUEL_' + syllabes[-1])
	try    : feature_list.append(u'SYLLABE_QUI_PRECEDE_' + syllabes[j - 1])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_PRECEDE2_' + syllabes[j - 2])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_PRECEDE3_' + syllabes[j - 3])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_PRECEDE4_' + syllabes[j - 4])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_SUIT_' + syllabes[j + 1])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_SUIT2_' + syllabes[j + 2])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_SUIT3_' + syllabes[j + 3])
	except : pass
	try    : feature_list.append(u'SYLLABE_QUI_SUIT4_' + syllabes[j + 4])
	except : pass

	# châine de caractères au niveau du vocable qui précède et celui qui suit
	try : feature_list.append(u'PREFIXE_DU_TOKEN_QUI_PRECEDE_' + tokens[i-1][0])
	except : pass
	try : feature_list.append(u'SUFFIXE_DU_TOKEN_QUI_PRECEDE_' + tokens[i-1][-1])
	except : pass
	try : ffeature_list.append(u'PREFIXE_DU_TOKEN_QUI_SUIT_' + tokens[i+1][0])
	except : pass
	try : ffeature_list.append(u'SUFFIXE_DU_TOKEN_QUI_SUIT_' + tokens[i+1][-1])
	except : pass

	# châine de caractères au niveau d'une phrase
	feature_list.append(u'TOKEN_ACTUEL_' + ''.join(syllabes))
	try    : feature_list.append(u'TOKEN_QUI_PRECEDE_' + ''.join(tokens[i - 1]))
	except : pass
	try    : feature_list.append(u'TOKEN_QUI_SUIT_' + ''.join(tokens[i + 1]))
	except : pass

	# Capitalization
	if syllabe[0].isupper():
		feature_list.append(u'CAPITALIZATION')

	# Number
	if re.search(r'\d', syllabe) is not None:
		feature_list.append(u'IL_Y_A_UN_CHIFFRE')

	# Punctuation
	punc_cat = set([u"Pc", u"Pd", u"Ps", u"Pe", u"Pi", u"Pf", u"Po"])
	if all (unicodedata.category(x) in punc_cat for x in syllabe):
		feature_list.append(u'PONCTUATION_PURE')

	return feature_list

def repr (c, null = "", spaces = False) :
	if not c : return null
	else :
		if spaces :
			return " " + rm_sep(c) + " "
		else:
			return rm_sep(c)

def rm_sep(str_in, seprator_in = code_seperator, replacing = u''):
	try :
		return str_in.replace(seprator_in, u"")
	except:
		try :
			return str_in.decode('utf-8').replace(seprator_in, replacing).encode('utf-8')
		except :
			try :
				return str_in.encode('utf-8').replace(seprator_in, replacing).decode('utf-8')
			except :
				raise

def chunking (token, mode) :

	chunks = []

	if mode == 0 :
	# sans segmenteur
		chunks.append(token)
	# segmentation à intervalle régulier
	else :
		token2 = unicodedata.normalize('NFD', token)
		seg = ""
		for c in token2 :
			seg += c
			if len(seg) == mode :
				chunks.append(seg)
				seg = ""
		if seg :
			chunks.append(seg)

	return chunks

def reshaping (token) :

	"""
	référence :
	http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
	"""

	token = unicodedata.normalize('NFD', token)
	#return token.lower()
	return token

def mode_position_encoder (token, position, mode_id, chunks, offset = 0, code_seperator_in = code_seperator) :

	mode_indicator = mode_indicators[mode_id]
	caracter_position_in_token = position + offset
	caracter_position_in_chunk = 0
	chunk_id = 0
	if mode_id == mode_names.index('insert') :
		chunk_position_limit_offset = 1
	else :
		chunk_position_limit_offset = 0
	chunk_position_limit = len(chunks[chunk_id]) + chunk_position_limit_offset

	for i in range(len(token) + 1):
		if i == caracter_position_in_token:
			mp_code = mode_indicator + code_seperator_in + str(caracter_position_in_chunk)
			return [mp_code, chunk_id]

		caracter_position_in_chunk += 1
		if caracter_position_in_chunk == chunk_position_limit :
			chunk_id += 1
			caracter_position_in_chunk = chunk_position_limit_offset
			chunk_position_limit = len(chunks[chunk_id]) + chunk_position_limit_offset

	return [None, None]

def entropy2 (dic, cnty, cntx, mode = 'token', unit = 'shannon') :

	# cntx : compteur pour la distribution des tokens
	# cnty : compteur pour la distribution des formes tonales
	# dic  : dicionnaire de correspondances entre chacun (en string)
	# 	 des tokens et la liste contenant chacune de ses formes tonales

	averaged_entropy = 0.0
	n = 0
	for n, token in enumerate(dic.keys()) :
		forms = dic[token]
		form_cnt = {form_tonal : cnty[form_tonal] for form_tonal in forms}
		if mode == 'occurrence' :
			averaged_entropy += entropy(form_cnt, unit) * cntx[token]
		else : # mode == "token"
			averaged_entropy += entropy(form_cnt, unit)

	averaged_entropy /= float(n + 1)

	if mode == 'occurrence' :
		averaged_entropy /= float(sum(cntx.values()))

	return averaged_entropy

def entropy (cnt, unit = 'shannon') :

	"""
	Reférence
	http://stackoverflow.com/questions/15450192/fastest-way-to-compute-entropy-in-python
	"""

	base = {
	        'shannon' : 2.,
	        'natural' : math.exp(1),
	        'hartley' : 10.
	}

	if len(cnt) <= 1:
		return 0

	len_data = sum(cnt.values())
	probs = [float(c) / len_data for c in cnt.values()]
	probs = [p for p in probs if p > 0.]
	ent = 0

	for p in probs:
		if p > 0.:
			ent -= p * math.log(p, base[unit])
	return ent

def sprint_cnt(cnt, prefix = "", num = -1, min = -1) :

	lst = cnt.most_common()
	if num > 0 :
		try :
			lst = lst[:num]
		except IndexError :
			pass
	if min > 0 :
		lst = [element for element in lst if element[1] >= min]

	try :
		return u"".join([prefix + ' '  + itm[0].encode('utf-8') + u' : ' + str(itm[1]).encode('utf-8') + u'\n' for itm in lst if itm])
	except :
		return u"".join([prefix + ' ' + itm[0] + u' : ' + str(itm[1]) + u'\n' for itm in lst if itm])

class statistique () :
	def __init__(self) :
		self.form_non_tonal = Counter()
		self.form_tonal     = Counter()
		self.code           = Counter()
		self.code2          = Counter()
		self.segment_code   = Counter()
		self.dict_code      = defaultdict()
		self.dict_form_tonal= defaultdict()
		self.num   = 0
		self.err_cnt = 0
		self.cnt_ops = 0
		self.mode = Counter()
		self.src_delete = Counter()
		self.dst_insert = Counter()

	def __str__(self) :

		ret  = u""
		ret += u"Over a corpus of {} word(s)\n".format(str(self.num))
		ret += u"Global Entropy\n"
		ret += u"\tE(Token)        = {:<6.2f} \n".format(entropy(self.form_non_tonal))
		ret += u"\tE(Tonalized Forme) = {:<6.2f} \n".format(entropy(self.form_tonal))
		ret += u"\tE(Resulting Code) = {:<6.2f} \n".format(entropy(self.code2))
		ret += u"\tr_E(Resulting Code) = {:<6.2f} \n".format(entropy(self.form_tonal)/entropy(self.code2))

		ret += u"Entropy by token (by average)\n"
                ret += u"\tE(Tonalized Form) = {:<6.2f} \n".\
			format(entropy2(self.dict_form_tonal, cnty = self.form_tonal, cntx = self.form_non_tonal))
                ret += u"\tE(Resulting Code) = {:<6.2f} \n".\
			format(entropy2(self.dict_code, cnty = self.code, cntx = self.form_non_tonal))
		ret += u"Levanshtein Distance between a tonalized form and its token (by average) = {:<6.2f} \n".format(self.cnt_ops / float(self.num))

		ret += u"Distribution over : \n"
		ret += u"\tEdit Operations : \n" + sprint_cnt(self.mode, u"\t\t",-1,20)
		ret += u"\tTotality of codes by chunk : \n" + sprint_cnt(self.code, u"\t\t",-1,20)
		ret += u"\tTotality of codes by edit operaiton : \n" + sprint_cnt(self.segment_code, u"\t\t",-1,20)
		ret += u"\tTotality of caracters deleted : \n" + sprint_cnt(self.src_delete, u"\t\t",-1,20)
		ret += u"\tTotality of caracters inserted : \n" + sprint_cnt(self.dst_insert, u"\t\t",-1,20)

		if self.err_cnt :
			ret += u"\nError : error rate in tone coding given by auto-verification = {}\n".format(self.err_cnt)
		return ret

class encoder_tones () :

	def __init__ (self) :
		self.src = ""
		self.dst = ""
		self.p_src = 0
		self.p_dst = 0
		self.ret = ""
		self.chunks = []
		self.stat = statistique()

	def delete(self) :
		mode_id = mode_names.index("delete")
		[mp_code, chunk_id] = mode_position_encoder(self.src,self.p_src, mode_id, self.chunks)
		segment = mp_code + code_seperator
		caracter_src = self.src[self.p_src]
		segment += caracter_src + code_seperator
		self.ret[chunk_id] += segment

		self.stat.cnt_ops += 1
		self.stat.mode["delete"] += 1
		self.stat.src_delete[caracter_src] += 1
		self.stat.segment_code[repr(segment)] += 1

	def insert(self) :
		mode_id = mode_names.index("insert")
		[mp_code, chunk_id] = mode_position_encoder(self.src,self.p_src, mode_id, self.chunks)
		segment = mp_code + code_seperator
		caracter_dst = self.dst[self.p_dst]
		segment += caracter_dst + code_seperator
		self.ret[chunk_id] += segment

		self.stat.cnt_ops += 1
		self.stat.mode["insert"] += 1
		self.stat.dst_insert[caracter_dst] += 1
		self.stat.segment_code[repr(segment)] += 1

	def differential_encode (self, form_non_tonal, form_tonal, chunk_mode) :

		self.p_src = -1
		self.p_dst = -1

		self.src = reshaping(form_non_tonal)

		if not self.src :
				return [[u""], [form_non_tonal]]

		self.chunks = chunking(self.src, chunk_mode)
		self.ret = [u"" for i in range(len(self.chunks))]

		self.dst = reshaping(form_tonal)
		ops = Levenshtein.editops(self.src, self.dst)
		self.stat.form_non_tonal[self.src] += 1
		self.stat.form_tonal    [self.dst] += 1
		self.stat.dict_form_tonal.setdefault(self.src, []).append(self.dst)

		for op in ops :

			mode, self.p_src, self.p_dst = op
			if mode == "delete" :
				self.delete()

			elif mode == "insert" :
				self.insert()

			else : # mode == "replace"
				self.insert()
				self.delete()

		# enlèvement du séparateur du code à la fin du chunk
		tmp = []
		for ret2 in self.ret :
			try :
				if ret2[-1] == code_seperator :
					ret2 = ret2[:-1]
			except IndexError:
				pass
			tmp.append(ret2)
		self.ret = tmp

		self.stat.num += 1
		repr_code = repr(u"".join(self.ret))
		self.stat.code[repr_code] += 1
		for chunk_code in self.ret :
			self.stat.code2[chunk_code] += 1
		self.stat.dict_code.setdefault(self.src, []).append(repr_code)

		# internal auto-check
		form_tonal_reproduced = repr(''.join([self.differential_decode(chunk, code) for code, chunk in zip(self.ret,self.chunks)]))
		if form_tonal_reproduced :
			form1 = reshaping(repr(unicodedata.normalize('NFD', form_tonal_reproduced)))
			form2 = reshaping(repr(unicodedata.normalize('NFD', form_tonal)))
			if form1 != form2 :
				self.stat.err_cnt += 1

		for code in self.ret :
			if not is_a_good_code :
				print "(encode) ouput code incorrect !";
				print code ;
				exit ()

		return [self.ret, self.chunks]

	def report (self) :
		print self.stat.__str__()

	def differential_decode (self, chunk, code) :

		chunk = reshaping(chunk)

		if len(code.strip()) == 0 : return chunk
		if not is_a_good_code(code) : print "(decode) input code incorrect !" ; print chunk ; print code ; exit()

		# if code[-1] == code_seperator : code = code[: -1]
		# code_segments = code.split(code_seperator)
		code_segments = split2(code,code_seperator)
		if len(code_segments) % 3 != 0 : print code ; print (code_segments) ; print ("input code incorrect !"); exit(1)

		p_offset = 0
		for i in range(0,len(code_segments),3) :
			try :
				m, p, c = code_segments[i:i+3]
			except :
				print (u"Bug 2 : {}".format(code))
				exit(1)

			p_eff = int(p) + p_offset
			if m == mode_indicators[mode_names.index('delete')] :
				try : l = chunk[: p_eff]
				except IndexError : l = ''
				try : r = chunk[p_eff + 1 :]
				except IndexError : r = ''
				chunk = l + r
				p_offset -= 1
			else : # elif m == mode_indicators[mode_names.index('insert')] :
				try : l = chunk[: p_eff]
				except IndexError : l = ''
				try : r = chunk[p_eff  :]
				except IndexError : r = ''
				chunk = l + c + r
				p_offset += 1

		return chunk


if __name__ == "__main__" : main()
