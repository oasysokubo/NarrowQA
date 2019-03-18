import nltk, operator, sys, re, csv
import gensim.downloader as api

from qa_engine.base import QABase
from qa_engine.score_answers import main as score_answers
from nltk.tree import Tree
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
from word2vec_extractor import Word2vecExtractor

#We've used the h prefix to indicate our created files
from h_chunking import chunking
import h_wordnet
import h_embeddings
import h_dependency
import h_constituency

STOPWORDS = set(nltk.corpus.stopwords.words("english"))

w2vecmodel = "data/glove-w2v.txt"
w2v = None
num_correct = 0
num_tried = 0

GRAMMAR =   """
            N: {<PRP>|<NN.*>}
            V: {<V.*>}
            ADJ: {<JJ.*>}
            NP: {<DT>? <ADJ>* <N>+}
            PP: {<IN> <NP>}
            VP: {<TO>? <V> (<NP>|<PP>)*}
            """

LOC_PP = set(["in", "on", "at", "under", "upon", "to", "along", "near", "in front of", "behind"])
TIME_PP = set({"on", "at", "was"})


#Allows for easy enable and disable of print statements 
def pprint(text):
    should_print = False
    if should_print == True:
        print(text)

def nns_filter(subtree):
    return subtree.label() == "nns"

# The standard NLTK pipeline for POS tagging a document
def get_sentences(text):
    sentences = nltk.sent_tokenize(text)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    return sentences

def get_text(question, story):
    stext = ""
    if question["type"] == "Sch":
        stext = story["sch"]
    else:
        stext = story["text"]
    qtext = question["text"]
    return qtext, stext

def get_bow(tagged_tokens, stopwords):
    return set([t[0].lower() for t in tagged_tokens if t[0].lower() not in stopwords])

# Get a lemmatized set of sentences
# Get a lemmatized set of sentences

def get_lem(sent):
    lmtzr = WordNetLemmatizer()
    sentences = []
    for token, tag in nltk.pos_tag(nltk.word_tokenize(sent)):
        sentences.append(lmtzr.lemmatize(token))
    return set(sentences)

def find_phrase(tagged_tokens, qbow):
    for i in range(len(tagged_tokens) - 1, 0, -1):
        word = (tagged_tokens[i])[0]
        if word in qbow:
            return tagged_tokens[i + 1:]

# Find best sentence by word overlapping method
def find_best_text2(qtype, qtext, story):
    if ("|" in qtype):
        sentences = get_sentences(story["sch"] + story["text"])
        story_tree = [Tree.fromstring(str(line)) for line in (story["sch_par"] + story["story_par"])]
    elif qtype == "Story":
        sentences = get_sentences(story["text"])
        story_tree = [Tree.fromstring(str(line)) for line in story["story_par"]]
    else:
        sentences = get_sentences(story["sch"])
        story_tree = [Tree.fromstring(str(line)) for line in story["sch_par"]]

    sents = list(zip(sentences, story_tree))
    qbow = get_bow(qtext, STOPWORDS)
    qlem = get_lem(qtext)
    
    answers = []
    # Check every sentence for the number of overlaps
    for sent in sents:
        sbow = get_bow(sent[0], STOPWORDS)
        slem = get_lem(sent[0])

        combo = qlem & sbow
        overlap = len(combo)
        answers.append((overlap, sent, sents.index(sent)))

    # Reverse list by the number of overlaps to get the best sentence at the head
    answers = sorted(answers, key=operator.itemgetter(0), reverse=True)

    best_tree = answers[0][1][1]
    best_sentence = (answers[0])[1][0]

    # Convert the tagged best_sentence into a joint regular sentence
    best_sentence = " ".join(word for word, tag in best_sentence)

    return best_sentence, best_tree, answers[0][2]

# Find best sentence by word overlapping method
def find_best_text(qtext, sents):

    qbow = get_bow(qtext, STOPWORDS)
    qlem = get_lem(qtext)
    
    answers = []
    # Check every sentence for the number of overlaps
    for sent in sents:
        sbow = get_bow(sent, STOPWORDS)
        slem = get_lem(sent)

        combo = qlem & sbow
        overlap = len(combo)
        answers.append((overlap, sent))

    # Reverse list by the number of overlaps to get the best sentence at the head
    answers = sorted(answers, key=operator.itemgetter(0), reverse=True)

    best_tree = answers[0][1][1]
    best_sentence = (answers[0])[1]

    return best_sentence


def check_sentences(question, answer):
    global num_tried
    global num_correct

    # correct = input("Correct? ")
    num_tried += 1
    #if int(answer_indexes[question["qid"]]) == index:
    num_correct += int(correct)
    # print("Current score: " + str(num_correct) + "/" + str(num_tried))

def lemmatize_word(word, tag):
    lmtzr = WordNetLemmatizer()
    if tag.startswith("V"):
        return lmtzr.lemmatize(word, 'v')
    else:
        return lmtzr.lemmatize(word, 'n')

def find_node(word, graph):
    for node in graph.nodes.values():   
        if node["word"] != None:
            if lemmatize_word(node["word"], node["tag"]) == word:
                return node
            if node["word"] == word:
                return node

    return None
    
def get_dependents(node, graph, excluded = []):
    results = []
    for item in node["deps"]:
        address = node["deps"][item][0]
        dep = graph.nodes[address]
        if dep['rel'] in excluded:
            continue
        results.append(dep)
        results = results + get_dependents(dep, graph)
        
    return results

def get_immediate_dependents(node, graph):
    results = []
    for item in node["deps"]:
        address = node["deps"][item][0]
        dep = graph.nodes[address]
        results.append(dep)

    return results

word_embedding_count = 0
word_overlap_count = 0
dependency_count = 0
chunking_count = 0
num_questions ={
    "who": 0,
    "what": 0,
    "when": 0,
    "where": 0,
    "why": 0,
    "how": 0,
    "had": 0,
    "what2": 0,
    "which": 0,
    "did": 0,
    "default": 0
}

def get_answer_type(qtext):
    global num_questions
    first_word = nltk.word_tokenize(qtext.lower())[0]
    second_word = nltk.word_tokenize(qtext.lower())[1]
    #TODO: Expand on What and Why question types
    #This looks inneficient, but it allows for easily modifying question type detection


    if first_word == "what":
        if second_word == "is" or second_word == "did" or second_word == "was" or second_word == "have":
            num_questions["what2"] += 1
            return "what2"
        num_questions["what"] += 1
        return "what"
    else:
        if first_word not in num_questions:
            return "default"

        num_questions[first_word] += 1
        return first_word
    return None

def get_best_candidates(question, story_info, atype):
    qmain = h_dependency.find_main(question["dep"])
    qword = lemmatize_word(qmain["word"], qmain["tag"])
    candidates = []

    sent_texts = nltk.sent_tokenize(story_info["text"])
    if atype == "what2":
        i = 0
        real_root = h_dependency.find_word_by_relation(qword, question["dep"], "root")
        if real_root is not None:
            qword = lemmatize_word(real_root["word"], real_root["tag"])

        nsubj_node = h_dependency.find_word_by_relation(qword, question["dep"], "nsubj")

        if nsubj_node == None:
            nsubj = qword
        else:
            nsubj = nsubj_node["word"]

        #TODO: Still messes up on "What was in a group of trees that was above the narrator?""
        for sgraph in story_info["dep"]:
            syns = h_wordnet.contains_synset(nsubj, sent_texts[i], story_info["sid"], check_hypo = True, check_hyper = True)
            if syns != None:        

                candidates.append(sent_texts[i])

            i+=1
        #input()
        if len(candidates) == 0:
            return sent_texts
        return candidates

    for sent in sent_texts:
        if atype == "where":
            has_loc_pp = False
            for word in nltk.word_tokenize(sent):
                if word in LOC_PP:
                    has_loc_pp = True
            if has_loc_pp == False:
                continue

        syns = h_wordnet.contains_synset(qword, sent, story_info["sid"], check_hypo = True, check_hyper = True)

        if syns != None:
            candidates.append(sent)
    if len(candidates) == 0:
        return sent_texts
    return candidates

def get_best_sentence(question, candidates, atype, story_id):
    sentence = ""

    qtext = question["text"]
    if question["difficulty"] == "Hard":
        qtext = h_wordnet.wordnet_sent(question["text"], story_id)


    #I thought this would be clever at first, but we just used h_embeddings for almost everything
    sentence_selection = {}
    sentence_selection["who"] = h_embeddings.word_embedding_sentence
    sentence_selection["what"] = h_embeddings.word_embedding_sentence    
    sentence_selection["what2"] = h_embeddings.word_embedding_sentence
    sentence_selection["when"] = h_embeddings.word_embedding_sentence
    sentence_selection["where"] = h_embeddings.word_embedding_sentence
    sentence_selection["why"] = h_embeddings.word_embedding_sentence
    sentence_selection["how"] = h_embeddings.word_embedding_sentence
    sentence_selection["had"] = h_embeddings.word_embedding_sentence    
    sentence_selection["which"] = h_embeddings.word_embedding_sentence

    if atype in sentence_selection:
        sentence = sentence_selection[atype](qtext, candidates)
    else:
        sentence = find_best_text(qtext, candidates)

    if sentence == "":
        sentence = find_best_text(qtext, candidates)
    return sentence

def extract_answer(question, sentence, sgraph, atype):    
    global dependency_count
    global chunking_count

    qgraph = question["dep"]
    answer = h_dependency.dependency_extract(qgraph, sgraph, atype)
    
    if answer == None:
        chunking_count+=1
        answer = chunking(question["text"], sentence)
    else:
        dependency_count += 1
    return answer

def get_answer(question, story):
    """
    :param question: dict
    :param story: dict
    :return: str

    question is a dictionary with keys:
        dep -- A list of dependency graphs for the question sentence.
        par -- A list of constituency parses for the question sentence.
        text -- The raw text of story.
        sid --  The story id.
        difficulty -- easy, medium, or hard
        type -- whether you need to use the 'sch' or 'story' versions
                of the .
        qid  --  The id of the question.


    story is a dictionary with keys:
        story_dep -- list of dependency graphs for each sentence of
                    the story version.
        sch_dep -- list of dependency graphs for each sentence of
                    the sch version.
        sch_par -- list of constituency parses for each sentence of
                    the sch version.
        story_par -- list of constituency parses for each sentence of
                    the story version.
        sch --  the raw text for the sch version.
        text -- the raw text for the story version.
        sid --  the story id
    """
    global word_embedding_count
    global word_overlap_count
    global dependency_count
    global chunking_count
    global num_questions
    answer = ""

    qtext, stext = get_text(question, story)

    """
    1. Get question type
    2. Get sch or story relevent info
    3. narrow down sentence selection
    4. select the best sentence based on question type
    5. extract answer from sentence based on question type
    """

    #### Get question type
    atype = get_answer_type(qtext)

    ### Get sch or story relevent info
    story_info = {}
    if question["type"] == "Sch":
        story_info["text"] = story["sch"]
        story_info["dep"] = story["sch_dep"]
        story_info["par"] = story["sch_par"]
    else:
        story_info["text"] = story["text"]
        story_info["dep"] = story["story_dep"]
        story_info["par"] = story["story_par"]
    story_info["sid"] = story["sid"]

    ### Narrow down sentence selection
    candidates = get_best_candidates(question, story_info, atype)

    ### Select the best sentence based on question type
    best_sentence = get_best_sentence(question, candidates, atype, story["sid"])
    
    ### Extract answer from sentence based on question type
    story_sents = nltk.sent_tokenize(story_info["text"])
    for sent in story_sents:
        if best_sentence == sent:
            index = story_sents.index(sent)
            sgraph = story_info["dep"][index]

    answer = extract_answer(question, best_sentence, sgraph, atype)
    return answer

class QAEngine(QABase):
    @staticmethod
    def answer_question(question, story):
        answer = get_answer(question, story)
        return answer

def run_qa(evaluate=False):
    QA = QAEngine(evaluate=evaluate)
    QA.run()
    QA.save_answers()

def main():
    # set evaluate to True/False depending on whether or
    # not you want to run your system on the evaluation
    # data. Evaluation data predictions will be saved
    # to eval-responses.tsv in the working directory.
    run_qa(evaluate=False)
    # You can uncomment this next line to evaluate your
    # answers, or you can run score_answers.py
    score_answers()

if __name__ == "__main__":
    main()
