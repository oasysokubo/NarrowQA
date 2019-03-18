import nltk, operator, sys, re, csv
from nltk.corpus import wordnet
from collections import defaultdict


STOPWORDS = set(nltk.corpus.stopwords.words("english"))

def load_wordnet_ids(filename):
    file = open(filename, 'r')
    if "noun" in filename: type = "noun"
    else: type = "verb"
    csvreader = csv.DictReader(file, delimiter=",", quotechar='"')
    word_ids = defaultdict()
    for line in csvreader:
        word_ids[line['synset_id']] = {'synset_offset': line['synset_offset'], 'story_'+type: line['story_'+type], 'stories': line['stories']}
    return word_ids

def contains_synset(word, text, story_id, check_hypo = False, check_hyper = False):

    verb_ids = load_wordnet_ids("wordnet/Wordnet_verbs.csv")
    noun_ids = load_wordnet_ids("wordnet/Wordnet_nouns.csv")

    word_synsets = wordnet.synsets(word)
    tokens = nltk.word_tokenize(text)



    for w, t in nltk.pos_tag(tokens):
        word_ids = []
        if t.startswith("N") or t.startswith("V") and w not in STOPWORDS:
            if t.startswith("V"):
                word_ids = verb_ids
                word_key = "story_verb"
            elif t.startswith("N"):
                word_ids = noun_ids
                word_key = "story_noun"


        
        token_synsets = wordnet.synsets(w)

        hypers = []
        hypos = []
        for syn in token_synsets:
            hypers.extend(syn.hypernyms())
            hypos.extend(syn.hyponyms())

        token_synsets.extend(hypers)
        token_synsets.extend(hypos)

        #Convert to just the word, not synset
        as_words = []
        for syn in token_synsets:
            if syn in word_synsets:# and syn.name() in word_ids and story_id + ".vgl" in word_ids[syn.name()]["stories"]:
                return w
        


    return None



# find synonyms, hyponyms, and hypernyms for the words
# used in the original story or in the Scheherazade output 
def wordnet_sent(qtext, story_id):
    #print("For story: " + str(story_id))
    #print("----------")
    verb_ids = load_wordnet_ids("wordnet/Wordnet_verbs.csv")
    noun_ids = load_wordnet_ids("wordnet/Wordnet_nouns.csv")

    i = 0
    qtokens = nltk.word_tokenize(qtext)
    for word, tag in nltk.pos_tag(qtokens):
        #print("For word: " + word)
        # print("{}: {}/{}".format(i, word, tag))
        if tag.startswith("N") or tag.startswith("V") and word not in STOPWORDS:
            if tag.startswith("V"):
                word_id = verb_ids
                word_key = "story_verb"
            elif tag.startswith("N"):
                word_id = noun_ids
                word_key = "story_noun"
            for synset_id, items in word_id.items():
                stories = items['stories']

            word_synsets = wordnet.synsets(word)

            for synset in word_synsets:
                #print("Looking at synset: " + str(synset))
                if synset.name() in word_id and story_id + ".vgl" in word_id[synset.name()]["stories"]:

                    #qtext[i] = (synset.name()[0:synset.name().index(".")], tag)
                    #print("[{}] {} was in word_ids for {}".format(word_id[synset.name()]["stories"], synset.name(), word))
                    qtokens[i] = word_id[synset.name()][word_key]

                for hypo in synset.hyponyms():

                    if hypo.name() in word_id and story_id + ".vgl" in word_id[hypo.name()]["stories"]:

                        #qtext[i] = (synset.name()[0:synset.name().index(".")], tag)
                        #print("[{}] {} was in word_ids for HYPO of {}".format(word_id[hypo.name()]["stories"], hypo.name(), word))
                        qtokens[i] = word_id[hypo.name()][word_key]

                for hyper in synset.hypernyms():

                    if hyper.name() in word_id and story_id + ".vgl" in word_id[hyper.name()]["stories"]:

                        #qtext[i] = (synset.name()[0:synset.name().index(".")], tag)
                        #print("[{}] {} was in word_ids for HYPER of {}".format(word_id[hyper.name()]["stories"], hyper.name(), word))
                        qtokens[i] = word_id[hyper.name()][word_key]

        #input()
        i+=1

    result = " ".join(qword for qword in qtokens)
    #print("Result: " + result)
    #input()
    return result

