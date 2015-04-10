# -*- coding: utf-8 -*-

import sqlite3
import marshal
import csv
import re

import inflection
from bs4 import BeautifulSoup

from .query import SearchQuery, SearchMatch, Entity



# XML Document documentation
# session -> mult. query

def get_entity_name(url):
    """
    :param url str:
    :return: entity_name
    Entity_name is the last part of the wiki url( after last /)
    """
    entity_name = ""
    for char_pos in range(len(url) - 1, 0, -1):
        if ( url[char_pos] == "/"):
            return entity_name
        entity_name = url[char_pos] + entity_name

def parse_xml(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f, ["lxml", "xml"])
        assert isinstance(soup, BeautifulSoup)
        return soup


def singularize_query(text):
    return " ".join([inflection.singularize(a) for a in text.split()])

class QueryParser():
    """
    A QueryParser stores and manages our queries.
    """
    def __init__(self, file_path):
        """
        :param file_path: path to xml file to be used
        """
        self.soup = parse_xml(file_path)
        self.query_array = []
        self._build_queries()

        # true positive, flase positives and false negatives (calculated in score.py>calc_tp_fp_fn)
        self.tp_s = self.tp_l = self.fp = self.fn = 0 

        #amount of queries and matches checked (also calculated in score.py>calc_tp_fp_fn)
        self.total_matches = 0
        self.queries_with_some_identical_true_entities = 0

    def get_all_queries_text(self):
        """
        :return: An array with the text of the queries
        """
        return [a.__repr__() for a in self.query_array]

    def _build_queries(self):
        """Populate our array of SearchQuery items.
        TODO: Add actual position and length of query of term in query
        Both Currently 0 by default
        """
        self.query_array = []
        for query in self.soup.find_all("query"):
            query_str = query.find_all("text")[0].text
            # query_str = query_str.strip().lower()
            #query_str = " ".join(c for c in query_str if c not in ('!','.',':', ','))
            new_query = SearchQuery(query_str)
            for ann in query.find_all("annotation"):
                try:
                    entity = Entity(get_entity_name(ann.find_all("target")[0].text), 1)
                except IndexError: # No true_entitiesntity here
                    #e = Entity("None", 0)
                    continue
                try:
                    span = ann.find_all("span")[0].text.replace('"', "")
                    # find the amount of word separators in the string before the occurence of span
                    #print(new_query.search_string, "=>", span)
                    str_before = re.match(r"\W*(.*)%s" % span, new_query.search_string.replace('"', ""), re.IGNORECASE)
                    print(str_before)
                    pos = len(re.findall(r"[\W]+", str_before.group(1), re.IGNORECASE))
                    assert(isinstance(pos, int))
                    new_match = SearchMatch(pos, len(span.split()), [entity], span)
                    new_match.chosen_entity = 0
                    new_query.true_entities.append(new_match)
                except Exception as e:
                    # raise e
                    print("Couldn't add \"%s\", there was some issue" % query_str)
                    new_query = None
                #print("LINK: " + e.link)
            if new_query:
                self.query_array.append(new_query)


def load_dict(file_path, fix=False):
    """
    :param file_path:
    :return:
    """
    conn = sqlite3.connect(file_path + "-db.db")
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE entity_mapping (words TEXT, entities BLOB)''')
        with open(file_path, "r", encoding='utf-8') as csvfile:
            crosswiki = csv.reader(csvfile, delimiter="\t")
            first_row = next(crosswiki)
            search_word = first_row[0]
            contents = []
            counter = 0
            c.execute('BEGIN TRANSACTION')
            for row in crosswiki:
                # Loop through all the rows in the csv
                if row[0] != search_word:
                    if contents:
                        c.execute('INSERT INTO entity_mapping VALUES(?, ?)', (search_word, marshal.dumps(contents)))
                        counter += 1
                    contents = []
                    search_word = row[0]
                if counter == 30000:  # Buffer insert queries and commit them at once
                    conn.commit()
                    counter = 0
                    c.execute('BEGIN TRANSACTION')
                # Split second part of csv - different separator from \t
                try:
                    row_ = row[1].split()
                except:
                    continue
                prob = row_[0]
                entity = row_[1]
                if fix:
                    if row[0].startswith(" ") or row[0].endswith(" "):
                        continue
                    entity = fix_entity(entity)
                # adding the entity and prob to the list as a dictionary
                contents.append((entity, prob))
            print("Database created")
    except sqlite3.OperationalError:
        print("Database already exists, cool!")
    return conn


def fix_entity(entity):
    assert isinstance(entity, str)
    entity = entity[0].upper() + entity[1:]
    return entity