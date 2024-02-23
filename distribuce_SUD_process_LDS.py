import pandas as pd
import distribuce_SUD_parser

def stringify_non_clausal_children(direct_children):
    """recursively creates a string of all children which do not belong to other clauses (==CUTS)"""

    clause_words = ""

    for child in direct_children:
        if child.comment != "clause":
            clause_words += child.form + "+"
            clause_words += stringify_non_clausal_children(child.direct_children)

    return clause_words


def list_non_clausal_children(direct_children):
    """recursively creates a list of all children (==nodes) which do not belong to other clauses (==CUTS)"""

    clause_words = []

    for child in direct_children:
        if child.comment != "clause":
            clause_words.append(child)
            clause_words += list_non_clausal_children(child.direct_children)

    return clause_words


def count_non_clausal_children(direct_children):
    """recursively counts all children which do not belong to other clauses (==CUTS)"""

    children_n = 0

    for child in direct_children:
        if child.comment != "clause":
            children_n += 1
            children_n += count_non_clausal_children(child.direct_children)

    return children_n


def count_non_clausal_children_length(direct_children):
    """recursively counts characters of all children (==their lengths) which do not belong to other clauses (==CUTS)"""

    children_length = 0

    for child in direct_children:
        if child.comment != "clause":
            children_length += len(child.form)
            children_length += count_non_clausal_children_length(child.direct_children)

    return children_length

def check_clausal_children(a_word):
    """checks whether any of direct children (==word node) is commented as 'clause'"""

    for child in a_word.direct_children:
        if child.comment != 'clause':
            return True  # can be processed because it governs a non-clausal phrase

    return False  # cannot be processed because it only governs other clauses

def check_root_predicate(a_sentence):
    """checks whether a sentence contains root which functions as a predicate"""

    for word in a_sentence.word_list:
        if word.deprel == 'root' and word.comment == 'clause':
            return True

    return False


def process_lds(a_clausal_head):
    """identifies a segment which words are linearly and syntactically connected"""

    clausal_lds = []
    current_lds = []
    clausal_nodes = list_non_clausal_children(a_clausal_head.direct_children)

    # if a clausal head is the only clausal node
    if len(clausal_nodes) == 0:
        current_lds.append(a_clausal_head)
        clausal_lds.append(current_lds)
        return clausal_lds

    # if a clause includes more than one node
    clausal_nodes.append(a_clausal_head)  # a list of all clausal nodes including the clausal head
    clausal_nodes.sort(key=lambda word_node: word_node.id)  # sorts the list according to ID of nodes in the ascending order

    for i in range(len(clausal_nodes) - 1):

        current_node = clausal_nodes[i]

        while current_node.next_node.deprel == 'punct':
            current_node = current_node.next_node

        # if a next node == linear neighbour and child
        if current_node.next_node == clausal_nodes[i + 1] and clausal_nodes[i].id == clausal_nodes[i + 1].parentID:
            current_lds.append(clausal_nodes[i])
        # if a next node == linear neighbour and parent
        elif current_node.next_node == clausal_nodes[i + 1] and clausal_nodes[i].parentID == clausal_nodes[i + 1].id:
            current_lds.append(clausal_nodes[i])
        # none of the conditions applies -> close a segment
        else:
            current_lds.append(clausal_nodes[i])
            clausal_lds.append(current_lds)
            current_lds = []

    # processes the last node of the clause (==renegade)
    current_lds.append(clausal_nodes[-1])
    clausal_lds.append(current_lds)

    return clausal_lds


def get_distribuce (a_treebank):
    """creates a distribution of LDS word forms, LDS syn. function and LDS length"""

    LDS_word_form = []
    LDS_deprel = []
    LDS_length = []
    for sentence in a_treebank.sentence_list:
        for word in sentence.word_list:
            if word.comment == 'clause':
                lds_list = process_lds(word)
                #LDS_length.append = len(process_lds(word))
                #print(LDS_length)
                for lds in lds_list:
                    lds_text = ' '.join(lds_word.form for lds_word in lds)
                    lds_deprel = ' '.join(lds_word.deprel for lds_word in lds)
                    LDS_word_form.append(lds_text)
                    LDS_deprel.append(lds_deprel)
                    length = 0

                    for lds_word in lds:
                        length += 1
                    LDS_length.append(length)


    LDS_word_dict = {}
    for LDS in LDS_word_form:
        if LDS in LDS_word_dict:
            LDS_word_dict[LDS] += 1
        else:
            LDS_word_dict[LDS] = 1

    LDS_word_dict = (dict(sorted(LDS_word_dict.items(), key=lambda x: x[1], reverse=True)))

    LDS_deprel_dict = {}
    for LDS in LDS_deprel:
        if LDS in LDS_deprel_dict:
            LDS_deprel_dict[LDS] += 1
        else:
            LDS_deprel_dict[LDS] = 1

    LDS_deprel_dict = (dict(sorted(LDS_deprel_dict.items(), key=lambda x: x[1], reverse=True)))

    LDS_length_dict = {}
    for LDS in LDS_length:
        if LDS in LDS_length_dict:
            LDS_length_dict[LDS] += 1
        else:
            LDS_length_dict[LDS] = 1

    LDS_length_dict = (dict(sorted(LDS_length_dict.items(), key=lambda x: x[0], reverse=False)))

    with open('LDS_word_form.txt', mode='w', encoding='utf-8') as output:
        print('word_form' + '\t' + 'frequency', file=output)
        for key, value in LDS_word_dict.items():
            print(str(key) + '\t' + str(value), file=output)

    with open('LDS_deprel.txt', mode='w', encoding='utf-8') as output:
        print('deprel' + '\t' + 'frequency', file=output)
        for key, value in LDS_deprel_dict.items():
            print(str(key) + '\t' + str(value), file=output)

    with open('LDS_length.txt', mode='w', encoding='utf-8') as output:
        print('length' + '\t' + 'frequency', file=output)
        for key, value in LDS_length_dict.items():
            print(str(key) + '\t' + str(value), file=output)

