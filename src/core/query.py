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

import re
class SearchQuery(object):
    def __init__(self, search_string):
        self.search_string = search_string
        self.array = re.findall(r"[\w]+", search_string)
        self.search_matches = []
        self.true_entities = []

    def add_match(self, match):
        # match: SearchMatch
        self.search_matches.append(match)

    def rank_matches(self):
        pass

    def __repr__(self):
        #return "<SearchQuery: %s>" % self.search_string
        return self.search_string

    def get_chosen_entities(self):
        return [m.entities[m.chosen_entity] for m in self.search_matches if m.chosen_entity >= 0]

    # def choose_best_entities(self):
    #     """
    #     TODO: Figure out a better way to do this
    #     """
    #     best_entities = {}
    #     for match in self.search_matches:
    #         substring, entity = match.choose_best_match()
    #         best_entities[substring] = entity
    #     return best_entities

    def get_search_string(self):
        return self.search_string

    def visualize(self):
        print("{:=^80}\nQuery: {:}{:}{:}\n".format("", TermColor.BOLD, self.search_string, TermColor.END, ""))
        for match in self.search_matches:
            print("{0:<25} | {1}".format(match.substring, match.entities[0]))
        print("-"*80 + "\n")

class SearchMatch(object):
    def __init__(self, position, word_count, entities, substring):
        self.substring = substring
        self.position = position
        self.word_count = word_count
        self.entities = entities
        self.chosen_entity = -1 # a positive number indicates array index 
                                # of chosen entity, -1 == no entity chosen
        self.rating = "" # "TP-strict", "TP-lazy", "FP", "FN"

    def __repr__(self):
        return "<SearchMatch: %s>[%r]<\\SearchMatch>" % (self.substring, self.entities[0])

    def get_chosen_entity(self):
        if self.chosen_entity >= 0:
            return self.entities[self.chosen_entity]
        else:
            return None

    def get_entities_limit(self, size_limit=5, prob_limit=None):
        """
        """
        if prob_limit:
            ents = [e for e in self.entities if e.probability >= prob_limit]
        else:
            ents = self.entities
        if not size_limit or len(ents) <= size_limit:
            return ents
        else:
            return ents[:size_limit]

    # def choose_best_match(self):
    #     """
    #     """
    #     return self.substring, self.entities[0]

class Entity(object):
    def __init__(self, link, probability):
        self.link = link
        self.probability = float(probability)

    def __repr__(self):
        return "<Entity: %s %f>" % (self.link, self.probability)
