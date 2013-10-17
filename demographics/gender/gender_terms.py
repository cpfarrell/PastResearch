#!/usr/bin/python

#Collection of terms that predominantly refer to one gender or the other

class GenderTerms:
  def __init__(self):
    self.male_terms = None
    self.female_terms = None

  def get_male_terms(self):
    if not self.male_terms:
      self.male_terms = set([
        "boyfriend",
        "husband",
        "boy",
        "bro"
        ])
    return self.male_terms

  def get_female_terms(self):
    if not self.female_terms:
      self.female_terms = set([
        "girlfriend",
        "wife",
        "gf",
        "girl"
        ])
    return self.female_terms
