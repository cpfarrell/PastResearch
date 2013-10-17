import math
from itertools import count

#Third party modules
import numpy as np

#Attensity media modules
import helper
import GetWords

#Index ngrams seen
ngram_id = count()

class TweetWithDemo:

    def __init__(self, user, line=None, max_tweets = -1):
        self.texts = []
        self.gender = ""
        self.name = ""
        self.username = user.lower()
        self.ngram_ids = set([])

        if line is not None:
            self.name = line["Name"]
            if 'texts' in line:
                texts = line["texts"]
                for text in texts:
                    #Allow for limiting the number of tweets collected
                    if len(self.texts) >= max_tweets and max_tweets >= 0:
                        break
                    #Don't store retweets
                    #if not self.is_retweet(text):
                    self.texts.append(text.lower())
            if "Gender" in line:
                self.gender = line["Gender"]
            if "Gender_Tag" in line:
                self.gender_tag = line["Gender_Tag"]

    #Create ngrams from tweet and username. Currently supports making word or character ngrams from tweet message and character ngrams from username
    def create_ngrams(self, max_tweets, min_tweet_words, max_tweet_words, min_name_words, max_name_words, min_username_chars, max_username_chars):
        ngrams = set([])

        if max_tweet_words>0:
            for idx, text in enumerate(self.texts):
                if idx >= max_tweets and max_tweets>= 0:
                    break
                words = GetWords.get_words_tokenized(text)
                clean_words = GetWords.clean_words(words)
                for ngram in helper.make_multi_ngrams(clean_words, Min=min_tweet_words, Max=max_tweet_words, prepend="T"):
                    ngrams.add(ngram)
        if max_name_words > 0:
            for ngram in helper.make_multi_ngrams(self.name.lower(), Min=min_name_words, Max=max_name_words, prepend="N"):
                ngrams.add(ngram)
        if max_username_chars>0:
            for ngram in helper.make_multi_ngrams(self.username, Min=min_username_chars, Max=max_username_chars, prepend="U"):
                ngrams.add(ngram)
        return ngrams


    #Determine if tweet is retweet
    def is_retweet(self, text):
        return text[0:2] =="RT"


#Hold Ngrams and any possible demographic information associated with them
class NgramsWithDemo:

    def __init__(self):
        self.male_count =0
        self.female_count = 0
        #If used in building matrix the column it corresponds to
        self.Id = next(ngram_id)


    def increment_gender(self, gender):
        if gender == "male":
            self.male_count += 1
        elif gender == "female":
            self.female_count += 1


    def get_gender_count(self, gender):
        if gender == "male":
            return self.male_count
        elif gender == "female":
            return self.female_count


    def significance(self, ngrams):        
        female_total = ngrams["TOTALGENDERCOUNTER"].get_gender_count("female")
        male_total = ngrams["TOTALGENDERCOUNTER"].get_gender_count("male")
        female_average = float(self.female_count)/female_total
        male_average = float(self.male_count)/male_total
        difference = female_average - male_average
        Uncertainty = math.sqrt((female_average/female_total) + (male_average/male_total))
        return difference/Uncertainty

