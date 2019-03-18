

#from qa import get_sentences


# See if our pattern matches the current root of the tree
def matches(pattern, root):
    # Base cases to exit our recursion
    # If both nodes are null we've matched everything so far
    if root is None and pattern is None: 
        return root
    # We've matched everything in the pattern we're supposed to (we can ignore the extra
    # nodes in the main tree for now)
    elif pattern is None:                
        return root
    # We still have something in our pattern, but there's nothing to match in the tree
    elif root is None:                   
        return None
    # A node in a tree can either be a string (if it is a leaf) or node
    plabel = pattern if isinstance(pattern, str) else pattern.label()
    rlabel = root if isinstance(root, str) else root.label()
    # If our pattern label is the * then match no matter what
    if plabel == "*":
        return root
    # Otherwise they labels need to match
    elif plabel == rlabel:
        # If there is a match we need to check that all the children match
        # Minor bug (what happens if the pattern has more children than the tree)
        for pchild, rchild in zip(pattern, root):
            match = matches(pchild, rchild) 
            if match is None:
                return None 
        return root
    return None
    
def pattern_matcher(pattern, tree):
    for subtree in tree.subtrees():
        node = matches(pattern, subtree)
        if node is not None:
            return node
    return None


def find_best_pattern(qtext):
    if get_sentences(qtext)[0][0][0] == "Where":
        return "(PP)"
    elif get_sentences(qtext)[0][0][0] == "Why":
        return "(NP (*) (PP))"
    elif get_sentences(qtext)[0][0][0] == "When":
        return "(PP)"
    elif get_sentences(qtext)[0][0][0] == "Who":
        # There are other cases (Person, place, a thing)
        if("about" in qtext): return "(NN)"
        return "(NP)"
    elif get_sentences(qtext)[0][0][0] == "What":
        # There are other cases
        return "(NP)"
    elif get_sentences(qtext)[0][0][0] == "How":
        return "(ADVP)"
    else:
        return "(NP)"