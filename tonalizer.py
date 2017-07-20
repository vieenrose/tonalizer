#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, re, codecs, time, os, collections, argparse, itertools, unicodedata, sys, fnmatch

from nltk.tag.crf import CRFTagger
import pycrfsuite

from differential_tone_coding import \
	apply_filter_to_base_element, \
	get_features_customised, get_duration, \
	sampling, csv_export, unzip, encoder_tones, \
	accuray2, get_sub_tone_code_of_sentence, \
	accumulate_tone_code_of_dataset, \
	reshape_tokens_as_sentnece, \
	make_tokens_from_sentence, \
	make_features_from_tokens
import fileReader

sys.stdin = codecs.getreader('utf8')(sys.stdin)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)


def main():

	aparser = argparse.ArgumentParser(description=u'Tonalisation basée sur l\'apprentissags automatique')
	aparser.add_argument('-v', '--verbose', help='Verbose output', default=False, action='store_true')
	aparser.add_argument('-l', '--learn', help='Learn model from data (and save as F if provided)', default=None)

	aparser.add_argument('-e', '--evalsize', help='Percent of training data with respect to training and test one (default 10)', default=10, type=float)
	aparser.add_argument('-c', '--chunkmode', help='Chunking mode specification which is effective only for tone (default 3)', default=3, type=int)

	aparser.add_argument('-d', '--diacritize', help='Use model F to diacritize raw text', default=None)
	aparser.add_argument('-f', '--filtering', help='Keep only one insertion for one poistion', default=False, action='store_true')


	aparser.add_argument('-m','--markers' , help='custumed set of markers to learn' , default=None, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-i','--infile' , help='Input file (.txt)' , default=sys.stdin, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-o','--outfile', help='Output file (.txt)', default=sys.stdout, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-s', '--store', help='Store evaluation resault in file (.csv) for further research purpose', default=None)

	args = aparser.parse_args()

	if not (args.learn or (args.diacritize and args.outfile and args.infile)) :
		aparser.print_help()
		exit(0)

	if args.verbose :
		print 'Arguments received by script'
		dico = vars(args)
		for key,val in dico.items():
			typeName = type(val).__name__
			sys.stdout.write(u"\t{} = {} ".format(key, val))
			if val :
				sys.stdout.write(u"({})".format(typeName))
			print ""

	if args.learn :

		print 'Make list of files'
		path = u"../Tashkeela-arabic-diacritized-text-utf8-0.3/texts.txt/"

		allfiles = []
		for root, dirnames, filenames in os.walk(path):
		    for filename in fnmatch.filter(filenames, u'*.txt'):
		        allfiles.append(os.path.join(root, filename))

		#fr = fileReader.fileReader(u"".join([unichr(x) for x in range(0x064B, 0x0652 + 1)]))
		fr = fileReader.fileReader(args.markers)
		allsents = []
		print 'Making observation data from disambiggated corpus of which'
		for infile in allfiles:
			if infile :
				print u'\t', infile
				sent = []
				for sentence in fr.read(infile) :
					for token in sentence :
						sent.append((token[0], token[1].encode('utf-8')))

					if len(sent) > 1:
						allsents.append(sent)
						sent = []

		print 'Token segmentation and tonal informaiotn compression'
		enc = encoder_tones()
		allsents2 = allsents
		allsents = []
		for sent in allsents2 :
			sent2 = []
			for token_tags in sent :
				token, tags = token_tags
				[codes, syllabes] = enc.differential_encode(token, tags.decode('utf-8'), args.chunkmode)
				token2 = [(syllabe, code.encode('utf-8')) for syllabe, code in zip(syllabes, codes)]
				sent2.append(token2)
			allsents.append(sent2)

		if args.verbose :
			enc.report()

		p = (1 - args.evalsize / 100.0)
		train_set, eval_set = sampling(allsents, p)
		print 'Split the data in train (', len(train_set),' sentences) / test (', len(eval_set),' sentences)'



		print 'Building classifier (pyCRFsuite)'
		# Initialization
		t1 = time.time()

		# A.1. Initialiser un nouveau modèle CRF
		tagger = CRFTagger(verbose = args.verbose, training_opt = {'feature.minfreq' : 10})
		trainer = pycrfsuite.Trainer(verbose = tagger._verbose)
		trainer.set_params(tagger._training_options)
		model_name = args.learn

		# A.2. Mettre à plat les structures de données pour préparer l'entrâinement contextuel
		for sent in train_set :
			[tokens, labels] = make_tokens_from_sentence(sent, True)
			features = make_features_from_tokens(tokens, True)
			labels = get_sub_tone_code_of_sentence(sent, sel_en = args.filtering)
			labels = list(itertools.chain(*labels))

			trainer.append(features, labels)
		trainer.train(model = model_name)

		print "... done in", get_duration(t1_secs = t1, t2_secs = time.time())

		# B. Evaluation
		print 'Evaluating classifier'
		gold_set = eval_set
		predicted_set_acc = list()

		# B.1. Charger le modèle CRF pour une des quatre phases d'annoation tonale
		tagger = CRFTagger(verbose = args.verbose, training_opt = {'feature.minfreq' : 10})
		trainer = pycrfsuite.Trainer(verbose = tagger._verbose)
		trainer.set_params(tagger._training_options)
		tagger.set_model_file(args.learn)

		# B.2 Annotation automatique syllabe par syllabe pour une phrase
		predicted_set = list()
		for p, sent in enumerate(gold_set) :

			[tokens, gold_labels] = make_tokens_from_sentence(sent, True)
			features = make_features_from_tokens(tokens, True)
			labels = tagger._tagger.tag(features)
			labels = reshape_tokens_as_sentnece(labels, sent)

			predicted_tokens = list()
			for i, token in enumerate(sent) :
				predicted_tokens.append(map(list, zip(tokens[i], labels[i])))
			predicted_set.append(predicted_tokens)

		# B.3 Accumuler en ordonner l'annotation syllabique
		if not predicted_set_acc :
			predicted_set_acc = \
				[[[['',''] for syllabe in token] for token in sent] for sent in predicted_set]

		predicted_set_acc = accumulate_tone_code_of_dataset (predicted_set_acc, predicted_set)
		predicted_set = predicted_set_acc

		if args.filtering :
			gold_set = apply_filter_to_base_element(gold_set, sel_en = args.filtering)

		print "Accuracy : {:>5.3f}".format(accuray2(gold_set, predicted_set, True))

		if args.store :
			stored_filename = args.store
			csv_export(stored_filename, gold_set, predicted_set, True)

		if args.verbose and args.store :
			print ("Tagged result is exported in {}".format(args.store))

	elif args.diacritize and args.infile and args.outfile :

		pass
		"""
		tagger = CRFTagger()
		try :
			html_parser.read_file(args.infile)
		except IOError:
			print "Error : unable to open the input file {} !".format(args.infile)
			exit(1)
		try :
			myzip = zipfile.ZipFile(args.diacritize, 'r')
		except IOError:
			print "Error : unable to open the model file {} !".format((args.diacritize + '.zip'))
			exit(1)

		num_phases = 2 * len(mode_indicators)
		taggers = []
		enc = encoder_tones()
		for phase in range(num_phases) :
			taggers.append(CRFTagger())
			taggers[phase].set_model_file(args.diacrtize)
			os.remove(model_basename)
		myzip.close()

		for snum, sentence in enumerate(html_parser.glosses) :
			tokens = [enc.differential_encode(token.token, token.token, args.chunkmode)[1] for token in sentence[2]]
			for phase in range(num_phases) :
				features = make_features_from_tokens(tokens, phase, True)
				if taggers[phase]._model_file :
					taggers[phase]._tagger.set(features)
			for tnum, token in enumerate(sentence[2]) :
				options = list()
				if token.value and len(token.value) > 2:
					for nopt, option in enumerate(token.value[2]) :
						try: tag = option.form.encode('utf-8')
						except : tag = ''
						prob = marginal_tone(taggers, tnum, tokens, tag, token.token, sel_en = args.filtering, decomposition_en = False)
						options.append((prob, option))

					reordered_probs, reordered_options = unzip(sorted(options, key = lambda x : x[0], reverse = True))
					if args.select :
						prob_max = reordered_probs[0]
						reordered_options = tuple([reordered_options[i] for i, p in enumerate(reordered_probs) if p >= prob_max])
					html_parser.glosses[snum][1][tnum] = reordered_options

		try :
			#html_parser.write(args.outfile)
			print "Disambiggated resulat for {} is saved in {}".format(args.infile,args.outfile)
		except IOError:
			print "Error : unable to create the output file {} !".format(args.outfile)
		"""


if __name__ == '__main__':
	main()
