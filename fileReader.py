#! /usr/bin/env python
# coding=utf-8

import unicodedata,argparse,codecs,sys,re

def utf8_open(file, mode = 'r', encoding = 'utf-8') :

	if isinstance(file, type(sys.stdin)) :
		print u'\t','Info. I/O from standard tube'
		fid = file
	else :
		if isinstance(file, str) :
			print u'\t', file.decode(encoding)
		else :
        	        print u'\t', file

		try :
			fid = codecs.open(file, mode, encoding)
		except :
			print ("Error : unable to open file !")
			exit()

	return fid

class fileReader () :

	def __init__(self, customed_markers = "") :
		self.strp = \
			self.__get_cat_startwith('Zl') + \
			self.__get_cat_startwith('Zp') + \
			self.__get_cat_startwith('Zs') + '\n'
	        self.sep_sent  = \
			self.__get_cat_startwith('Pi') + \
			self.__get_cat_startwith('Pf') + \
			self.__get_cat_startwith('Po')
        	self.sep_token = \
			self.__get_cat_startwith('Zs')

		if not customed_markers :
			self.markers = self.__get_cat_startwith('Mn')
		else :
			self.markers = customed_markers
		#print "init."

	def read(self, filein) : # golden set

		pat1   = u'([{}]+)'.format(self.sep_sent)
		pat2   = u'[{}]+'  .format(self.sep_token)

		self.regex1 = re.compile(pat1, flags = re.IGNORECASE)
		self.regex2 = re.compile(pat2, flags = re.IGNORECASE)
		with utf8_open(filein) as file :
			sentences = list()
			for n, line in enumerate(file) :
				para = line.strip(self.strp)
				sents = self.regex1.split(para)
				for sent in sents :
					tokens = self.regex2.split(sent)
					sentence = list()
					for token in tokens :
						token_masked = self.__mask(token)
						if token and token_masked:
							sentence.append([token_masked, self.__unicode_decomp(token)])
					if sentence :
						sentences.append(sentence)
		return sentences

	def read2(self, filein, fileout) : # undiacritized

		with utf8_open(filein) as fidin :
			with utf8_open(fileout, 'w') as fidout :
				for line in fidin : fidout.write(self.__mask(line))

	def __unicode_decomp(self, str_in) :
		return unicodedata.normalize('NFD', str_in)

	def __mask(self, str_in) :
		str_in = self.__unicode_decomp(str_in)
		return u"".join([c for c in str_in if c not in self.markers])

	def __get_cat_startwith(self, str_in) :
		return u"".join([unichr(i) for i in xrange(sys.maxunicode) \
			if unicodedata.category(unichr(i)).startswith(str_in)])

def view_allsents(sentences) :
	s_num = 0
	for sent in sentences :
		if sent :
			t_num = 0
			for token in sent :
				if token :
					print u"{:6d}{:3d}: '{}' -> '{}'".format(s_num,t_num,token[0],token[1])
					t_num += 1
			s_num += 1
			print

if __name__ == "__main__" :

	# interface en ligne de commande
	parser = argparse.ArgumentParser()
	parser.add_argument('file')
	args = parser.parse_args()

	fr = fileReader()
	sentences = fr.read(args.file)
	view_allsents(sentences)
