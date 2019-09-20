# Main Idea:
#	- Text preprocessing (removing stopwards, removing punctuation, etc.)
# 	- Frequency talbe of words/Word Frequency distribution - how many times each word appears in the document
#	- Score each sentence depending on the words it contains and the frequency table
# 	- build summary by joining ever sentence above a certain score limit

import spacy 
from spacy.lang.en.stop_words import STOP_WORDS
import wikipedia
from string import punctuation
from heapq import nlargest

TEST_WIKI_ARTICLE = 'Albert Einstein'

wikipedia.set_lang('en')
document_1 = str(wikipedia.page(TEST_WIKI_ARTICLE).content)

# if this line doesn't work run 'python -m spacy download en'
nlp = spacy.load('en')
docx = nlp(document_1)

### Word frequency table
# 		dictionary of words and their counts using non stop words

word_freq = {}
for word in docx:
	w = word.text
	w = w.strip(punctuation)
	w = w.lower()
	# stopword omission
	if w not in STOP_WORDS:
		if w not in word_freq:
			word_freq[w] = 0
		word_freq[w] += 1

### Maximum frequency
max_freq = max(word_freq.items(), key=lambda x: x[1])[1]

for (word, freq) in word_freq.items():
	word_freq[word] = freq/max_freq 

### Sentence scores
# 		scoring every sentence based on the number of words
# 		(non-stop words in our word freq table)

sentence_list = [sentence for sentence in docx.sents]

max_sentence_len = 30

sent_scores = {}
for sent in sentence_list:
	for word in sent:
		w = word.text.lower()
		if w in word_freq:
			if len(sent.text.split(' ')) < max_sentence_len:
				if sent not in sent_scores:
					sent_scores[sent] = 0
				sent_scores[sent] += word_freq[w]
 
num_sentences_in_summary = 7
summarized_sentences = nlargest(num_sentences_in_summary, sent_scores, key=sent_scores.get)

# convert spacy span to string
final_sentences = [ s.text.strip() for s in summarized_sentences]
final_summary = '. '.join(final_sentences)

print(final_summary)


