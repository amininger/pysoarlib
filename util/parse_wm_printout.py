
def parse_wm_printout(text):
    """ Given a printout of soar's working memory, parses it into a dictionary of wmes, 
        Where the keys are identifiers, and the values are lists of wme triples rooted at that id

    :param text: The output of a soar print command for working memory
    :type text: str

    :returns dict{ str, list[ (str, str, str) ] }

    """

    ### First: preprocess the output into a string of tokens
    tokens = []
    quote = None
    for word in text.split():
        # Handle quoted strings (Between | |)
        if word[0] == '|':
            quote = word
        elif quote is not None:
            quote += ' ' + word
        if quote is not None:
            if len(quote) > 1 and quote.endswith('|'):
                tokens.append(quote)
                quote = None
            elif len(quote) > 1 and quote.endswith('|)'):
                tokens.append(quote[:-1])
                quote = None
            continue

        # Ignore operator preferences
        if word in [ '+', '>', '<', '!', '=' ]:
            continue
        # Ignore activation values [+23.000]
        if word.startswith("[+") and (word.endswith("]") or word.endswith("])")):
            continue
        # Ignore singleton lti's  (@12533)
        if word.startswith("(@") and word.endswith(")"):
            continue
        # Strip opening parens but add $ to indicate identifier
        if word.startswith("("):
            word = '$' + word[1:]

        # Don't care about closing parens
        word = word.replace(")", "")
        tokens.append(word)

    wmes = dict()
    cur_id = None
    cur_att = None
    cur_wmes = []
    i = 0

    for token in tokens:
        if len(token) == 0:
            continue
        # Identifier
        if token[0] == '$':
            cur_id = token[1:]
            cur_att = None
            cur_wmes = []
            wmes[cur_id] = cur_wmes
        # Attribute
        elif token[0] == '^':
            cur_att = token[1:]
        # Value
        elif cur_id is None:
            print("ERROR: Value " + token + " encountered with no id")
        elif cur_att is None:
            print("ERROR: Value " + token + " encountered with no attribute")
        else:
            cur_wmes.append( (cur_id, cur_att, token) )
    
    return wmes

