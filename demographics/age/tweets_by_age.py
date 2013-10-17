# tweets_by_gender.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# script to find users by gender and pull tweets from their accounts
#
# first step in building test database for gender
#

# core modules
import sys
import time
import itertools
import random


# non-standard modules
import twitter
import nltk
import re

# attensity media modules
sys.path.append('../../social_apis/twitter/')
import py_twitter
sys.path.append('../UserDatabase/')
import user_database

def main():
    # parameters
    tweets_per_user = 15
    initial_page = 1
    twitter_api_sleep_time = 10
    count = 20
    max_follower_count = 5000
    max_friend_count = 2000

    #Put output in redis database
    user_db = user_database.UserDatabase()

    twitter_api = py_twitter.Twitter_Client()

    for i in range(15, 65):
        print "Looking for age " + str(i)
        page = initial_page
        empty_searches = 0

        #If four consecutive searches come up empty probably outside of relevant users
        while empty_searches < 4:
            time.sleep(twitter_api_sleep_time)
            print "Searching for page " + str(page)
            users = twitter_api.search_user_names(str(i) + " year old", page=page, count=count)

            #End of results
            if 'errors' in users:
                break

            user_found = False

            for user in users:
                # attempt to weed out businesses and celebrities
                if user['lang'] != 'en' or user['followers_count'] > max_follower_count or user['friends_count'] > max_friend_count:
                    continue
                screen_name = user['screen_name']
                description = user['description']

                #Lots of false matching from "X year old in a Y year old's body" so lets remove anything with body in it
                if 'body' in description.lower():
                    continue

                age = find_age(description)
                if age>0:
                    #Don't look for users with tweets already stored but record that they were identified by first name
                    if user_db.user_has_tweets(screen_name):
                        results_dict = {'age': age, 'description': description}
                        user_db.add_user_info(screen_name, results_dict)
                        user_db.add_user_identifier("PERSONKNOWNWITHAGEOF_" + str(age), screen_name)
                        user_db.add_user_identifier("AgeKnown", screen_name)
                        user_found = True
                        continue
                            
                    # account found, pull a post
                    #  careful about api limits
                    time.sleep(twitter_api_sleep_time)

                    # occassionally crashes with TwitterError, let's catch them and continue
                    try:
                        results = twitter_api.search(screen_name, count=50)
                    except twitter.TwitterError, e:

                        print e
                        print 'Continuing...'
                        continue

                    tw_count = 0
                    tweets = []
                            
                    # note this does not guarantee we'll find one tweet per user
                    for result in results:
                        # log of how many tweets we had to check
                        tw_count += 1

                        # verify tweet is from user, not directed to user
                        search_result = result.AsDict()
                        if search_result['user']['screen_name'] == screen_name:
                            tweets.append(search_result['text'])

                            if len(tweets) > tweets_per_user:
                                break

                    #Don't use users we didn't find any tweets from
                    if len(tweets) == 0:
                        continue

                    #Add user to database with meta data
                    results_dict = {'age': age, 'Name': user['name'], 'description': description, 'texts': tweets}
                    user_db.add_user_info(screen_name, results_dict)
                    user_db.add_user_identifier("PERSONKNOWNWITHAGEOF_" + str(age), screen_name)
                    user_db.add_user_identifier("AgeKnown", screen_name)
                    user_db.add_user_with_tweets(screen_name)
                    user_found = True

                    #Put 5% of tweets into test database
                    if random.randint(0, 20) == 1:
                        user_db.add_user_test_sample(screen_name)

            if not user_found:
                empty_searches += 1
            else:
                empy_searches = 0

            page += 1

def find_age(description):
    description = standardize(description)
    for sentence in split_sentences(description):
        words = sentence.split()
        #Looks for something like "28 year old" at beginning of sentence
        if len(words)>3 and re.match("^[\d]+$", words[0]) and words[1]=="year" and words[2]=="old":
            return words[0]

        #Looks for something like "im 28 year old" anywhere in description 
        for idx, word in enumerate(words[:-3]):
            if word=="im" and re.match("^[\d]+$", words[idx+1]) and words[idx+2]=="year" and words[idx+3]=="old":
                return words[idx+1]
    return 0
    

#Try to standardize what to look for
def standardize(text):
    text = text.lower()
    text = text.replace("years", "year")
    text = text.replace("i'm", "im")
    text = text.replace("i am", "im")
    text = text.replace("im a", "im")
    return text

def split_sentences(description):
    sentences = []
    front = 0
    for idx, letter in enumerate(description):
        if letter in [",", "."]:
            sentences.append(description[front:idx])
            front = idx + 1

    #Need to add last string
    if front != (len(description)-1):
        sentences.append(description[front:len(description)-1])
    return sentences

if __name__ == '__main__':
    main()
