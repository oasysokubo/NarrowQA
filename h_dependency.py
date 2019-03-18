import nltk, operator, sys, re, csv
from nltk.stem.wordnet import WordNetLemmatizer


LOC_PP = set(["in", "on", "at", "under", "upon", "to", "along", "near", "in front of", "behind"])




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

def find_main(graph):
    for node in graph.nodes.values():
        if node['rel'] == 'root':
            return node
    return None

def find_word_by_relation(word, qgraph, relation):
    qmain = find_node(word, qgraph)
    qword = word
    #qword = qmain['lemma']
    #print(qword)

    if relation in qmain["deps"]:
        index = qmain["deps"][relation][0]
        return qgraph.nodes[index]
    else:
        #print(relation + " not in ")
        #for node in qmain["deps"]:
        #    print(str(node))
        return None

def get_by_address(address, sgraph):
    for node in sgraph.nodes.values():
        if node["address"] == address:
            return node



def dependency_extract(qgraph, sgraph, qtype=None):
    #print("Question graph: " + str(qgraph))
    #print("Sgraph: " + str(sgraph))
    res = None
    qmain = find_main(qgraph)
    qword = qmain["word"]
    #qword = qmain['lemma']
    #print(qword)
    snode = find_node(lemmatize_word(qword, qmain["tag"]), sgraph)

#    print("Question type: " + qtype + " focused on word: " + qword)

    if snode == None:
        #print("Couldnt find snode for: " + str(qword))
        #print("Sgraph: " + str(sgraph))
        return None
    elif qtype == "what":        

        #TODO: Any "What" question needs to be based on the VBD whos nsubj matches the VBD's nsubj in the question
        #Possibly go to the head of the word and unpack there
        #First take the nsubj
        #
        #for node in sgraph.nodes.values():
            #if node['tag'] == "VBD":
                #deps = get_dependents(node, sgraph)
        """
        target_node = find_node(qword, sgraph)
        if target_node == None:
            return None
        print("Deps: ")
        de = get_immediate_dependents(target_node, sgraph)

        for d in de:
            print(str(d))
            if d["rel"] == "nsubj":
                nsubj = d
                print(d["word"] + " was nsubj of : " + target_node["word"])

        if nsubj is not None:
            deps = get_dependents(nsubj, sgraph)
            deps = sorted(deps+[nsubj], key=operator.itemgetter("address"))

            print("Answered as: " + " ".join(dep["word"] for dep in deps))
            #input()
            res = " ".join(dep["word"] for dep in deps)
        else:  

        """
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))

                    #print("Answered as: " + " ".join(dep["word"] for dep in deps))
                    #input()
                    res = " ".join(dep["word"] for dep in deps)
        """
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "advcl":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))

                    print("Answered as: " + " ".join(dep["word"] for dep in deps))
                    input()
                    return " ".join(dep["word"] for dep in deps)
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nsubj":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))

                    print("Answered as: " + " ".join(dep["word"] for dep in deps))
                    input()
                    return " ".join(dep["word"] for dep in deps)

        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))

                    print("Answered as: " + " ".join(dep["word"] for dep in deps))
                    input()
                    return " ".join(dep["word"] for dep in deps)
        """


    #TODO: Check for conj, if conj exists, need to add conj and dobj together before returning
    elif qtype == "what2":
        # print("WHAT DID QUESTION")

        #Needs to take the nmod:agent of the qword.
        for node in sgraph.nodes.values():
            if node['tag'] == "VBD":
                deps = get_immediate_dependents(node, sgraph)
                # for d in deps:
                #     if d['rel'] == "nsubj":
                #         print("Found : " + d['word'] + " as nsubj of: " + node['word'])

        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "ccomp":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)
                if node['rel'] == "dobj":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)



    elif qtype == "who":
        for node in sgraph.nodes.values():
            #If our keyword is a dobj, we likely don't care about the verb it related to
            #Nevermind, this lost more precision than it gained
            """
            if node['rel'] == "dobj":
                deps = get_dependents(node, sgraph)
                deps = sorted(deps+[node], key=operator.itemgetter("address"))
                return " ".join(dep["word"] for dep in deps)
            """

            if node.get('head', None) == snode["address"]:
                #print("Looking at node: " + node['word'])                

                if node['rel'] == "nsubj":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)



    elif qtype == "when":
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)


    #For where questions, we look for the LOC_PP, take its head, and grab all the dependants from there.
    elif qtype == "where":
        for node in sgraph.nodes.values():
            if node["word"] in LOC_PP:
                #print("NODE: " + str(node))
                address = node["head"]
                target = get_by_address(address, sgraph)
                if target == None:
                    return None
                #print("Target is: " + str(target))
                #Where questions do not need the advcl part attached to them. It is too much info
                deps = get_dependents(target, sgraph)
                deps = sorted(deps+[target], key=operator.itemgetter("address"))
                res = " ".join(dep["word"] for dep in deps)
                break;

    elif qtype == "why":
        #Dependency graphs are not suitable for answering Why questions
        return None


        """
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    return " ".join(dep["word"] for dep in deps)
        """

    elif qtype == "how":
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod:tmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)
    """
    else:
        for node in sgraph.nodes.values():
            if node.get('head', None) == snode["address"]:
                if node['rel'] == "nmod":
                    deps = get_dependents(node, sgraph)
                    deps = sorted(deps+[node], key=operator.itemgetter("address"))
                    res = " ".join(dep["word"] for dep in deps)
    """

    #if qtype == "who":
    #    print("Result: " + str(res))
        #input()
    return res

