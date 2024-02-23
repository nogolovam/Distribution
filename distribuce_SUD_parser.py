# FUNCTIONS FOR PROCESSING A TREEBANK FILE IN CONLLU FORMAT
def list_non_clausal_children(direct_children):
    """recursively creates a list of all children (==nodes) which do not belong to other clauses (==CUTS)"""

    clause_words = []

    for child in direct_children:
        if child.comment != "clause":
            clause_words.append(child)
            clause_words += list_non_clausal_children(child.direct_children)

    return clause_words

def stringify_non_clausal_children(direct_children):
    """recursively creates a string of all children which do not belong to other clauses (==CUTS)"""

    clause_words = ""

    for child in direct_children:
        if child.comment != "clause":
            clause_words += child.form + " "
            clause_words += stringify_non_clausal_children(child.direct_children)

    return clause_words


class Treebank:

    def __init__(self):
        self.sentence_list = []


class Sentence:

    def __init__(self):
        self.id = None
        self.text = None
        self.root = None
        self.word_list = []
        self.MDD_sentence = 0
        self.clause_list = []
        self.length_by_clause = 0

    def identify_clause_words(self):

        for word in self.word_list:
            if word.comment == 'clause':
                clause_words_form = stringify_non_clausal_children(word.direct_children)
                clause_words_form += word.form
                clause_nodes = list_non_clausal_children(word.direct_children)
                clause_nodes.append(word)
                new_clause = Clause()
                new_clause.word_list = clause_nodes
                new_clause.clause_form = clause_words_form
                self.clause_list.append(new_clause)
                self.length_by_clause = len(self.clause_list)


    def MDD_sentence_get(self):
        hodnoty=[]
        for word in self.word_list:
            if word.deprel != "root" and word.deprel != "punct":
                hodnoty.append(word.distance)
        if len(hodnoty)!= 0:
            self.MDD_sentence = sum(hodnoty)/len(hodnoty)

class Clause:

    def __init__(self):
        self.word_list = []
        self.pocet_LDS = 0
        self.MDD_clause = 0
        self.clause_form = []


    def MDD_clause_get(self):
        hodnoty=[]
        for word in self.word_list:
            if word.comment != "clause" and word.deprel != "punct":
                hodnoty.append(word.distance)
        if len(hodnoty)!= 0:
            self.MDD_clause = sum(hodnoty)/len(hodnoty)




class Word:

    def __init__(self):
        self.id = None
        self.form = None
        self.lemma = None
        self.upos = None
        self.xpos = None
        self.feats = None
        self.parentID = None
        self.parent = None
        self.deprel = None
        self.deps = None
        self.transliteration = None
        self.comment = None
        self.next_node = None
        self.direct_children = []
        self.all_children = []
        self.distance = 0


def create_worddata(a_line):
    """processes data from a word line"""

    new_word = Word()
    word_data = a_line.split('\t')
    new_word.id = int(word_data[0])
    new_word.form = str(word_data[1].strip()).lower()  # strip fc for arbitrary spaces #vždy bude malými písmeny
    new_word.lemma = word_data[2]
    new_word.upos = word_data[3]
    new_word.xpos = word_data[4]
    new_word.feats = word_data[5]
    new_word.parentID = int(word_data[6])
    new_word.deprel = word_data[7]
    new_word.deps = word_data[8]
    if new_word.deprel != "root" and new_word.deprel != "punct":
        new_word.distance = abs(new_word.parentID - new_word.id)
    if 'Translit' in a_line:
        new_word.transliteration = word_data[9].split('=')[-1].strip().lower()  # strip fc for arbitrary spaces

    return new_word

def load_treebank(filename):
    """opens conllu file, loads data and returns a treebank data structure"""

    a_treebank = Treebank()
    a_sentence = None

    with open(filename, mode='r', encoding='utf-8') as data:
        for line in data:
            if line.startswith('# sent_id'):  # sentence identification
                a_sentence = Sentence()
                a_sentence.id = line.split('=')[1].strip()
                a_treebank.sentence_list.append(a_sentence)
            if line.startswith('# text ='):  # text identification
                #a_sentence.text = line.strip()
                a_sentence.text = line[len('# text = '):].strip()
            if not line.startswith('#') and len(line) > 1:# reads LF character too
                text = line.split('\t')
                if text[0].find('-') == -1:
                    a_sentence.word_list.append(create_worddata(line))
                    a_sentence.MDD_sentence_get()
    return a_treebank


def assign_next_node(a_treebank):
    """adds a next node to word data"""

    for sentence in a_treebank.sentence_list:
        for i in range(len(sentence.word_list) - 1):
            sentence.word_list[i].next_node = sentence.word_list[i + 1]

            if (sentence.word_list[i].id + 1) != sentence.word_list[i + 1].id:
                raise ValueError('ERROR!')

    return a_treebank


def find_parent_and_children(a_treebank):  # NOTE: root parent is None!
    """interlinks the data based on the parent-child relationship"""

    for sentence in a_treebank.sentence_list:
        for word in sentence.word_list:
            if word.parentID != 0 and word.deprel != 'punct':
                word.parent = sentence.word_list[word.parentID - 1]  # assign a parent in the form of a word class
                word.parent.direct_children.append(word)  # add a child to its parent
            else:
                sentence.root = word

    return a_treebank


def add_word_to_all_parents(word, parent):
    """adds a word to all their parents from the bottom to top of the treebank data structure"""

    if parent is not None:
        parent.all_children.append(word)
        add_word_to_all_parents(word, parent.parent)


def find_all_children(a_treebank):
    """finds all nodes directly and indirectly dependent on a given word in the treebank data structure"""

    for sentence in a_treebank.sentence_list:
        for word in sentence.word_list:
            if word.deprel != 'punct':
                add_word_to_all_parents(word, word.parent)

    return a_treebank


def check_root_predicate(a_word):

    if a_word.deprel == 'root' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
        return True

    return False

def check_privlastek_predicate(a_word):

    if a_word.parent is not None and (a_word.parent.upos == 'NOUN' or a_word.parent.upos == 'PROPN') and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
        return True

    return False

def check_dependent_root_predicate(a_word):

    if a_word.parent is not None and a_word.parent.deprel == 'root' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
        if a_word.deprel != 'comp:aux':
            return True

    return False

def check_vedlejsi_predicate(a_word):
    #dát jako root vedlejší věty SCONJ? - vždy je to hlava te klauze - má nižší id, takže je výš

    #původní verze, kdy jsme tagovali predikát vedlejší věty
    '''if a_word.parent is not None and a_word.parent.upos == 'SCONJ' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
        if a_word.deprel != 'comp:aux':
            return True'''

    '''if a_word.upos == 'SCONJ':
        return True'''

    if a_word.upos == 'SCONJ':
        for child in a_word.direct_children:
            if (child.upos == 'VERB' or child.upos == 'AUX') and child.xpos[0:2] != 'Vf' and child.deprel != 'comp:aux':
                return True

    '''for child in a_word.direct_children:
        if (child.upos == 'VERB' or child.upos == 'AUX') and child.xpos[0:2] != 'Vf' and child.deprel != 'comp:aux':
            if child.parent is not None and child.parent.upos == 'SCONJ':
                return True'''

    return False

def check_predmetne_predicate(a_word):

    if a_word.parent is not None and a_word.parent.parent is not None:
        if (a_word.parent.parent.upos == 'VERB' or a_word.parent.parent.upos == 'AUX') and a_word.parent.parent.xpos[0:2] != 'Vf' and (a_word.parent.upos == 'VERB' or a_word.parent.upos == 'AUX') and a_word.parent.xpos[0:2] != 'Vf':
            if a_word.deprel != 'comp:aux' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
                return True

    return False

def check_predmetne_predicate_DET(a_word):

    if a_word.parent is not None and a_word.parent.upos == 'DET':
        if a_word.deprel != 'comp:aux' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
            return True

    return False

def check_predicate_on_predicate(a_word):
    if a_word.parent is not None and (a_word.parent.upos == 'VERB' or a_word.parent.upos == 'AUX') and a_word.parent.xpos[0:2] != 'Vf' and a_word.parent.deprel != 'comp:aux':
        if a_word.deprel != 'comp:aux' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
            return True

    return False

def check_predmetne_predicate_SCONJ(a_word):

    if a_word.parent is not None and a_word.parent.parent is not None:
        if a_word.parent.parent.upos == 'SCONJ' and (a_word.parent.upos == 'VERB' or a_word.parent.upos == 'AUX') and a_word.parent.xpos[0:2] != 'Vf':
            if a_word.deprel != 'comp:aux' and (a_word.upos == 'VERB' or a_word.upos == 'AUX') and a_word.xpos[0:2] != 'Vf':
                return True

    return False

def check_predmetne_predicate_inf(a_word):

    if (a_word.upos == "VERB" or a_word.upos == "AUX") and a_word.xpos[0:2] != "Vf":
        if a_word.parent is not None and a_word.parent.upos == "VERB" and a_word.parent.xpos[0:2] == "Vf":
            return True

    return False

def check_coordinate_clause(a_word):

    if a_word.parent is not None and a_word.parent.parent is not None:
        if a_word.parent.upos == 'CCONJ' and (a_word.parent.parent.upos == 'VERB' or a_word.parent.parent.upos == 'AUX') and a_word.parent.parent.xpos[0:2] != 'Vf':
            if (a_word.upos == "VERB" or a_word.upos == "AUX") and a_word.xpos[0:2] != "Vf" and a_word.deprel != 'comp:aux':
                return True

    return False

def tag_predicate(a_treebank):
    """adds a clausal comment to words which are predicates"""

    for sentence in a_treebank.sentence_list:
        for word in sentence.word_list:
            if check_root_predicate(word):
                word.comment = 'clause'
            if check_privlastek_predicate(word):
                word.comment = 'clause'
            if check_dependent_root_predicate(word):
                word.comment = 'clause'
            if check_vedlejsi_predicate(word):
                word.comment = 'clause'
            if check_predmetne_predicate(word):
                word.comment = 'clause'
            if check_predmetne_predicate_DET(word):
                word.comment = 'clause'
            if check_predmetne_predicate_SCONJ(word):
                word.comment = 'clause'
            if check_predmetne_predicate_inf(word):
                word.comment = 'clause'
            if check_predicate_on_predicate(word):
                word.comment = 'clause'
            if check_coordinate_clause(word):
                word.comment = 'clause'

    for sentence in a_treebank.sentence_list:
        sentence.identify_clause_words()
        for clause in sentence.clause_list:
            clause.MDD_clause_get()
    return a_treebank


def tag_conj_predicates(a_treebank):
    """looks for words which depend on the root-predicate (only!), carry conj dependency relation and also meet criteria for the predicate function,
       if such a word is found, it is tagged as the predicate (via comment atribute)"""

    for sentence in a_treebank.sentence_list:
        for word in sentence.word_list:
            if word.deprel == 'conj' and word.parent is not None and (word.parent.upos == 'VERB' or word.parent.upos == 'AUX') and word.parent.xpos[0:2] != 'Vf':
                if (word.upos == 'VERB' or word.upos == 'AUX') and word.xpos[0:2] != 'Vf':
                    word.comment = 'clause'


    return a_treebank


def create_treebank(filename):
    """combines all the functions and returns a complete treebank data structure"""

    a_treebank = load_treebank(filename)
    a_treebank = assign_next_node(a_treebank)
    a_treebank = find_parent_and_children(a_treebank)
    a_treebank = find_all_children(a_treebank)
    # a_treebank = tag_clause_head(a_treebank)
    # a_treebank = tag_coordinate_clause(a_treebank)
    a_treebank = tag_predicate(a_treebank)
    a_treebank = tag_conj_predicates(a_treebank)

    return a_treebank