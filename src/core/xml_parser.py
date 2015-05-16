# -*- coding: utf-8 -*-

import sqlite3
import marshal
import csv
import re
from urllib.request import unquote

from bs4 import BeautifulSoup, CData
import inflection

from .query import SearchQuery, SearchMatch, Entity, SearchSession

# XML Document documentation
# session -> mult. query

FIX_STRING = False

wiki_base = "http://en.wikipedia.org/wiki/"


def extract_entity_name(url):
    """
    :param url str:
    :return: entity_name
    Entity_name is the last part of the wiki url( after last /)
    """
    assert isinstance(url, str)
    entity_name = url.replace(wiki_base, "")
    return unquote(entity_name)


def parse_xml(file_path):
    with open(file_path) as f:
        soup = BeautifulSoup(f, ["lxml", "xml"])
        assert isinstance(soup, BeautifulSoup)
        return soup


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

        # amount of queries and matches checked (also calculated in score.py>calc_tp_fp_fn)
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
        for session in self.soup.find_all("session"):
            session_id = session["id"]
            search_session = SearchSession(session_id)

            for query in session.find_all("query"):
                query_str = unquote(query.find_all("text")[0].text)

                # Replacing quotes for now
                # They could be potentially useful for queries as with quotes it's known the words
                # have to be connected by an &
                query_str = query_str.replace('"', '')

                new_query = SearchQuery(query_str, search_session)
                new_query.with_double_quotes = unquote(query.find_all("text")[0].text)
                curr_pos = 0
                for ann in query.find_all("annotation"):
                    ann_spann = ann.span
                    try:
                        entity_str = unquote(extract_entity_name(ann.find_all("target")[0].text))
                        entity = Entity(entity_str, 1)
                    except IndexError:  # No true_entities here
                        curr_pos += len(ann.find_all("span")[0].text.split())

                        continue
                    try:
                        match_str = unquote(ann.find_all("span")[0].text)
                        match_str = match_str.replace('"', "")
                        # find the amount of word separators in the string before the occurence of span
                        # str_before = re.match(r"\W*(.*)%s" % match_str, new_query.search_string.replace('"', ""),
                        #                       re.IGNORECASE)
                        # position = len(re.findall(r"[\W]+", str_before.group(1), re.IGNORECASE))
                        position = curr_pos
                        curr_pos += len(ann.find_all("span")[0].text.split())

                        assert (isinstance(position, int))

                        new_match = SearchMatch(position, len(match_str.split()), [entity], match_str)
                        new_match.chosen_entity = 0
                        new_query.true_entities.append(new_match)
                    except Exception as e:
                        print("Couldn't add \"%s\" to %s, there was some issue" % (ann, query_str))
                        new_query = None

                if new_query:
                    self.query_array.append(new_query)
                    search_session.append(new_query)


class QueryOutput():
    """
    Generate XML file from annotation results.
    """

    def __init__(self, target_file):
        self.target_file = target_file
        self.soup = BeautifulSoup(features='xml')
        self.webscope = self.soup.new_tag("webscope")

    def write_session(self, name):
        return self.soup.new_tag("session", id=name)

    def cdata(self, text):
        return CData(str(text))

    def write_match(self, match):
        """
        Generate the <annotation> tag
        """
        match_xml = self.soup.new_tag("annotation")
        span = self.soup.new_tag("span")
        span.append(self.cdata(match.substring))
        entity = match.get_chosen_entity()
        match_xml.append(span)
        if entity:
            target = self.soup.new_tag("target")
            target.append(self.cdata(wiki_base + entity.link))
            match_xml.append(target)
        return match_xml

    def write_query(self, query):
        """
        Generate the <query> tag
        """
        s_tag = self.soup.find(id=query.session.session_id)
        if not s_tag:
            s_tag = self.write_session(name=query.session.session_id)
            starttime = "1"
        else:
            queries = s_tag.find_all("query")
            if not queries:
                starttime = "1"
            else:
                starttime = 1
                for q in queries:
                    if int(q["starttime"]) > starttime:
                        starttime = int(q["starttime"])
                starttime = str(starttime + 1)
        query_xml = self.soup.new_tag("query", starttime=starttime)
        text = self.soup.new_tag("text")
        text.append(self.cdata(query.search_string))
        query_xml.append(text)
        for match in query.search_matches:
            query_xml.append(self.write_match(match))
        s_tag.append(query_xml)
        self.webscope.append(s_tag)

    def commit(self):
        """
        Save file to disk.
        """
        self.soup.append(self.webscope)
        with open(self.target_file, "wb") as file:
            file.write(self.soup.prettify("utf-8"))
            file.close()


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
            # first_row = next(crosswiki)
            search_word = None
            first = True
            contents = []
            counter = 0
            for row in crosswiki:
                # Loop through all the rows in the csv
                if row[0] != search_word:
                    if contents:
                        c.execute('INSERT INTO entity_mapping VALUES(?, ?)', (search_word, marshal.dumps(contents)))
                        print('inserting stuff')
                    contents = []
                    search_word = row[0]
                # Split second part of csv - different separator from \t
                try:
                    row_ = row[1].split()
                except:
                    continue
                prob = row_[0]
                entity = row_[1]
                # if fix:
                #     if row[0].startswith(" ") or row[0].endswith(" "):
                #         continue
                #     entity = fix_entity(entity)
                # adding the entity and prob to the list as a dictionary
                if search_word == "0":
                    print(entity)
                contents.append((entity, prob))
            conn.commit()
            print("Database created")
    except sqlite3.OperationalError:
        print("Database already exists, cool!")
    return conn


def load_wiki_names(file_path):
    """
    :param file_path:
    :return:
    """
    # assert isinstance(str, file_path)
    conn = sqlite3.connect(file_path + "-db.db")
    c = conn.cursor()
    i = 0
    try:
        c.execute('''CREATE TABLE entity
             (wihki_title TEXT)''')

        with open(file_path, "r", encoding='utf-8') as csvfile:
            # this is a csv reader
            names = csv.reader(csvfile, delimiter="\t")

            for row in names:
                c.execute('INSERT INTO entity VALUES(?)', (row[0], ))  # , (row[0], re.sub("[^\w\s]", " ", row[0])

        conn.commit()
        print("Database created")

    except sqlite3.OperationalError:
        print("Database already exists, cool!")

    return conn
