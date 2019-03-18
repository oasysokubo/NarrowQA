import nltk, operator, sys, re, csv
from word2vec_extractor import Word2vecExtractor
from nltk.stem.wordnet import WordNetLemmatizer


from qa import pprint
from qa import lemmatize_word




w2vecmodel = "data/glove-w2v.txt"
w2v = None



def word_embedding_sentence(qtext, sentences):
    global w2v


    if w2v is None:
        print("loading word vectors ...", w2vecmodel)
        w2v = Word2vecExtractor(w2vecmodel)


    #print("QText before lemma: " + qtext)
    qlemma = " ".join(lemmatize_word(w, t) for w, t in nltk.pos_tag(nltk.word_tokenize(qtext)))
    #print("Qtext after lemma: " + qlemma)
    #input()



    best = ""
    best_score = -100
    for sent in sentences:

        slemma = " ".join(lemmatize_word(w, t) for w, t in nltk.pos_tag(nltk.word_tokenize(sent)))

        q_vec = w2v.sen2vec(qtext.lower())
        s_vec = w2v.sen2vec(slemma.lower())
        score = w2v.w2vecmodel.cosine_similarities(q_vec, [s_vec])

        #print("[{}], {}".format(score, slemma))
        if score > best_score:
            best_score = score
            best = sent


    return best
    