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

	aparser = argparse.ArgumentParser(description=u'Tonalizer - CRF-based Tone Reconstitution Tool')
	aparser.add_argument('-v', '--verbose', help='Verbose output', default=False, action='store_true')
	aparser.add_argument('-l', '--learn', help='Learn model from diacritized text (and save as file if provided)', default=None,  type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-e', '--evalsize', help='Percent of training data with respect to training and test one (default 10)', default=10, type=float)
	aparser.add_argument('-c', '--chunkmode', help='Word segmentation width (default 3)', default=3, type=int)
	aparser.add_argument('-d', '--diacritize', help='Use model file to diacritize a raw text', default=None)
	aparser.add_argument('-u', '--undiacritize', help='Undiacritize a raw text', default=False, action='store_true')
	aparser.add_argument('-f', '--filtering', help='Keep only one insertion for one poistion', default=False, action='store_true')
	aparser.add_argument('-m','--markers' , help='Custumed set of markers to learn' , default=None, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-i','--infile', help='Input file (.txt)' , default=sys.stdin, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-o','--outfile', help='Output file (.txt)', default=sys.stdout, type=lambda s: unicode(s, 'utf8'))
	aparser.add_argument('-s', '--store', help='Store evaluation result in file (.csv), effective only in learning mode', default=None, type=lambda s: unicode(s, 'utf8'))
	args = aparser.parse_args()

	if not (args.learn or args.diacritize or args.undiacritize) :
		print 'Error : choose -learn, -diacritize or -undiacritize !'
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

	if args.undiacritize :
		fr = fileReader.fileReader(args.markers)
		fr.read2(args.infile, args.outfile)

	elif args.learn :
		fr = fileReader.fileReader(args.markers)
		allsents = []
		print 'Making observation data from diacritized text'
		for sentence in fr.read(args.infile) :
			sent = []
			for token in sentence :
				sent.append((token[0], token[1].encode('utf-8')))
			if len(sent) > 1:
				allsents.append(sent)

		print 'Word segmentation and diacritic informaiotn compression'
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

		# A.1. Initialize a new CRF trainer
		tagger = CRFTagger(verbose = args.verbose, training_opt = {'feature.minfreq' : 10})
		trainer = pycrfsuite.Trainer(verbose = tagger._verbose)
		trainer.set_params(tagger._training_options)

		# A.2. Prepare training set
		for sent in train_set :
			[tokens, labels] = make_tokens_from_sentence(sent, True)
			features = make_features_from_tokens(tokens, True)
			labels = get_sub_tone_code_of_sentence(sent, sel_en = args.filtering)
			labels = list(itertools.chain(*labels))

			trainer.append(features, labels)
		trainer.train(args.learn.encode('utf-8'))

		print "... done in", get_duration(t1_secs = t1, t2_secs = time.time())

		# B. Evaluation
		print 'Evaluating classifier'
		gold_set = eval_set
		predicted_set_acc = list()

		# B.1. Load trained model
		tagger = CRFTagger(verbose = args.verbose, training_opt = {'feature.minfreq' : 10})
		trainer = pycrfsuite.Trainer(verbose = tagger._verbose)
		trainer.set_params(tagger._training_options)
		tagger.set_model_file(args.learn.encode('utf-8'))

		# B.2 Tagging segment by segment
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

		# B.3 Assemble segements to get annotated token
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
			print ("Tagged result is exported in {}".format(args.store.encode('utf-8')))

	elif args.diacritize and args.infile and args.outfile :

		# todo : store and load chunkmode value

		# A.1. Load a CRF tagger
		tagger = CRFTagger()
		tagger.set_model_file(args.diacrtize.encode('utf-8'))

		# Making observation data from undiacritized text
		fr = fileReader.fileReader(args.markers)
		allsents = []
		print 'Making observation data from diacritized text'

		# non-processed token -> non-processed sentence
		for sentence in fr.read(args.infile) :
			sent = []
			for token in sentence :
				sent.append(token[1]) # token[1] : non-processed token from a undiacritized text
			if len(sent) > 1:
				allsents.append(sent)

		# Word segmentation
		enc = encoder_tones()
		allsents2 = allsents
		allsents = []
		for sent in allsents2 :
			sent2 = []
			for token in sent :
				# here, we use encode as a simple chunker to get segment level
				[NONE, chunks] = enc.differential_encode(token, token, args.chunkmode)
				# put (chunk,chunk) instead of chunk to fit the input format of "make_tokens_from_sentence"
				token2 = [(chunk, chunk) for chunk in chunks]
				sent2.append(token2)
			allsents.append(sent2)

		# A.2 Tagging segment by segment
		predicted_set = list()
		for p, sent in enumerate(allsents) :

			[tokens, NONE] = make_tokens_from_sentence(sent, True)
			features = make_features_from_tokens(tokens, True)
			labels = tagger._tagger.tag(features)
			labels = reshape_tokens_as_sentnece(labels, sent)

			predicted_tokens = list()
			for i, token in enumerate(sent) :
				predicted_tokens.append(map(list, zip(tokens[i], labels[i])))
			predicted_set.append(predicted_tokens)

	        # simple raw file writer
		enc = encoder_tones()
		with utf8_open(args.outfile, 'w') as fidout :
			for sent in predicted_set :
				for token in sent :
					for syllabe in token :
						# syllabe[0], syllabe[1] -> token by chunk, label by chunk
						form += enc.differential_decode(syllabe[0], syllabe[1].decode('utf-8'))
					fidout.write(form + u' ')
				fidout.write(u'\n')

		try :
			print "Disambiggated resulat for {} is saved in {}".format(args.infile,args.outfile)
		except IOError:
			print "Error : unable to create the output file {} !".format(args.outfile)


if __name__ == '__main__':
	main()
