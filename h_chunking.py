import nltk, operator, sys, re, csv
from nltk.tree import Tree

GRAMMAR =   """
            N: {<PRP>|<NN.*>}
            V: {<V.*>}
            ADJ: {<JJ.*>}
            NP: {<DT>? <ADJ>* <N>+}
            PP: {<IN> <NP>}
            VP: {<TO>? <V> (<NP>|<PP>)*}
            """

LOC_PP = set(["in", "on", "at", "under", "upon", "to", "along", "near", "in front of", "behind"])
TIME_PP = set({"on", "at"})

def pp_filter(subtree):
    return subtree.label() == "PP"

def np_filter(subtree):
    return subtree.label() == "NP"

def chunking(qtext, sentence):
    tokens = nltk.word_tokenize(qtext)
    token_sent = nltk.word_tokenize(sentence)
    tagged_sent = nltk.pos_tag(nltk.word_tokenize(sentence))

    chunker = nltk.RegexpParser(GRAMMAR)
    first_word = tokens[0].lower()
    tree = chunker.parse(tagged_sent)

    ans = sentence
    #Who questions
    if first_word == "who":
    
        for t in tree.subtrees(filter=np_filter):
            last = t.leaves().pop()
            if last[0].istitle():
                ans = last[0]

    #What questions
    elif first_word == "what":
        subject = None

    #When questions
    elif first_word == "when":
        # print("When question")
        for t in tree.subtrees(filter=pp_filter):
            #print("Subtree: " + str(t))
            ans = " ".join(token[0] for token in t.leaves())

    #Where questions
    elif first_word == "where":
        for t in tree.subtrees(filter=pp_filter):
            #print("Subtree: " + str(t))
            if t[0][0] in LOC_PP:
                #print("Subtree: " + str(t))
                ans = " ".join([token[0] for token in t.leaves()])

    elif first_word == "why":
        for word in token_sent:
            if word == "because":
                return " ".join(t for t in token_sent[token_sent.index(word):len(token_sent)-1])
        for word in nltk.word_tokenize(sentence):
            if word == "to":
                return " ".join(t for t in token_sent[token_sent.index(word):len(token_sent)-1])

    elif "did" == first_word or "had" == first_word:
        words = nltk.word_tokenize(sentence.lower())
        if 'not' in words or 'never' in words or 'no' in words:
            return 'no'
        else:
            return 'yes'

    return ans