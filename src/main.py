# -*- coding: utf-8 -*-

import os

from baseline import baseline
from core.xml_parser import QueryParser
from core.score import lazy_F1


THIS_FILE = os.path.realpath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
DATA_DIR = THIS_DIR + "/../data/"
TRAIN_XML = "query-data-short-set.xml"
DICT = "crosswikis-dict-preprocessed"


def main():
    parser = QueryParser(DATA_DIR + TRAIN_XML)


    # for query in parser.soup.find_all("query"):
    # 	#text = query.find_all("text")[0].text
    # 	# text = query.find('annotation')
    # 	# if (text is not None):
    # 	# 	print(text.text)

    db_conn = baseline.load_dict(DATA_DIR + DICT)
    
    for q in parser.query_array:
    #for q in parser.get_all_queries_text():
        #print(q.true_entities)
        entities = baseline.search_entities(q, db_conn)

    for q in parser.query_array:
        q.visualize()
	
	#evaluate baseline solution
    lazy_F1(parser)
	

if __name__ == "__main__":
    main()
