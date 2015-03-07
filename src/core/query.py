# -*- coding: utf-8 -*-
class TermColor:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class SearchQuery(object):
    def __init__(self, search_string):
        self.search_string = search_string
        self.array = search_string.split()
        self.search_matches = []

    def add_match(self, match):
        # match: SearchMatch
        self.search_matches.append(match)

    def rank_matches(self):
        pass

    def __repr__(self):
        #return "<SearchQuery: %s>" % self.search_string
        return self.search_string

    def choose_best_entities(self):
        """
        TODO: Figure out a better way to do this
        """
        best_entities = {}
        for match in self.search_matches:
            substring, entity = match.choose_best_match()
            best_entities[substring] = entity
        return best_entities

    def get_search_string(self):
        return self.search_string

    def visualize(self):
        print("{:=^80}\nQuery: {:}{:}{:}\n".format("", TermColor.BOLD, self.search_string, TermColor.END, ""))
        for substr, entity in self.choose_best_entities().items():
            print("{0:<25} | {1}".format(substr, entity))
        print("-"*80 + "\n")

class SearchMatch(object):
    def __init__(self, position, entities, substring):
        self.substring = substring
        self.position = position
        self.entities = entities

    def __repr__(self):
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, self.entities)

    def choose_best_match(self):
        """
        """
        return self.substring, self.entities[0]

class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)