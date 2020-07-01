
def parse_wm_printout(text):
    """ Given a printout of soar's working memory, parses it into a dictionary of wmes, 
        Where the keys are identifiers, and the values are lists of wme triples rooted at that id

    :param text: The output of a soar print command for working memory
    :type text: str

    :returns dict{ str, list[ (str, str, str) ] }

    """
    text = text.replace("\n", " ")
    text = text.replace(")", "") # Don't care about closing parentheses
    tokens = [ word.strip() for word in text.split() ]
    wmes = dict()
    cur_id = None
    cur_wmes = []
    i = 0

    while i < len(tokens):
        token = tokens[i]
        i += 1
        # Ignore operator preferences
        if token in [ '+', '>', '<', '!', '=' ]:
            continue
        # Beginning of new identifier section
        if token[0] == '(':
            cur_id = token[1:]
            cur_wmes = []
            wmes[cur_id] = cur_wmes
            continue
        # Expecting an attribute
        if token[0] != '^':
            print("UNEXPECTED TOKEN for " + cur_id + ": " + token)
            continue
        attr = token[1:]
        val = tokens[i]
        i += 1
        # Check for multi-word quoted strings surrounded by |
        if val[0] == '|':
            cur_word = val
            while cur_word[-1] != '|':
                cur_word = tokens[i]
                i += 1
                val += ' ' + cur_word
        cur_wmes.append( (cur_id, attr, val) )
    
    return wmes

