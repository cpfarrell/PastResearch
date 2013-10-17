#tag_gender.py
#Attempt to tag gender of people by them being identified by someone else's tweet
#Code takes as input a file containing data drawn from the attensity pipeline.
#Write's to redis database
#Chris Farrell 03 July 2013

#Standard modules
import sys
import argparse
import nltk
import json
import simplejson
from collections import defaultdict
import re

#Attensity media modules
sys.path.append('../UserDatabase/')
import gender_terms
import user_database

#Remove hashtag symbol
def remove_hashtags(words):
    count = 0
    while count != len(words):
        if words[count] == '#':
            del words[count]
        else:
            count += 1

#Take tweet sentences and see if anyone's gender can be identified
#Looks for phrasing of "my [GENDER TERM] @USERNAME"
#Currently deals with contradictory labeling by taking last one found, should be improved but likely only a small effect
#Keeps the username and gender found and adds user to appropriate sets
def find_gender(words, male_terms, female_terms, users):    
    for i in xrange(1, len(words)-3):
        username = words[i+3]
        
        #Database can't handle when screen name is identifier and it is obviously a bad flag
        if username in male_terms or username in female_terms or username == "FirstName":
            continue

        #Make sure screen name correct format, meaning alphanumeric or underscore only
        if not re.match(r'^[A-Za-z0-9_]+$', username):
            continue

        GenderKnown = False

        if words[i]=="my" and words[i+1] in male_terms and words[i+2]=="@":
            users.add_user_info(username, {"Gender": "male"})
            GenderKnown = True

        if words[i]=="my" and words[i+1] in female_terms and words[i+2]=="@":
           users.add_user_info(username, {"Gender": "female"})
           GenderKnown = True

        #Identify this user as part of sets
        if GenderKnown:
            users.add_user_identifier(words[i+1], username)
            users.add_user_identifier("GenderTerm", username)
            users.add_user_identifier("GenderKnown", username)
            users.add_user_not_searched(username)

#No argument runs whole file
def main(filename, max_size):
    f = open(filename, 'r')

    gt = gender_terms.GenderTerms()
    male_terms = gt.get_male_terms()
    female_terms = gt.get_female_terms()

    users = user_database.UserDatabase()

    for idx, line in enumerate(f):
        #Break if pass max size
        if idx > max_size and max_size>0:
           break

        if idx%10000 == 0:
            print idx

        json_dict = json.loads(line)

        sentences = nltk.sent_tokenize(json_dict['title'].lower())

        for sentence in sentences:
            words = nltk.word_tokenize(sentence)
            remove_hashtags(words)
            find_gender(words, male_terms, female_terms, users)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', dest='filename',
                        help='File containing jsons of output from the attensity pipeline', default=None)
    parser.add_argument('-s', '--size', dest='max_size', type=int,
                        help='Number of lines to process in file, default processes whole file', default=-1)

    args = parser.parse_args()

    if args.filename is None:
        print 'Did not specify input file.'
        sys.exit(1)

    main(args.filename, args.max_size)
