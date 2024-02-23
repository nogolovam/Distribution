import distribuce_SUD_parser
import distribuce_SUD_process_LDS as S

def export_data(treebank_file):
    """creates a treebank data structure, calls functions for processing given linguistic levels"""

    a_treebank = distribuce_SUD_parser.create_treebank(treebank_file)

    S.get_distribuce(a_treebank)

export_data('C:/Users/Michaela/Disk Google/Doktorat/distribuce/treebanky/SUD/dohromady_SUD.conllu')