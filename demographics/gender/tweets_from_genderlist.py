# tweets_from_genderlist.py
# Written by:  Chris Farrell
#              chris.farrell@attensitymedia.com
#
# script to find pull tweets from accounts of people of known gender
#
#


# core modules
import sys
import time
import itertools
import random

sys.path.append('../../social_apis/twitter/')

# non-standard modules
import simplejson
import twitter

# attensity media modules
import py_twitter
import gender_terms
sys.path.append('../UserDatabase/')
import user_database

def get_tweets(users, twitter_api, screen_name, gender):

    #Parameters
    tweets_per_user = 15
    twitter_api_sleep_time = 10

    #  careful about api limits
    time.sleep(twitter_api_sleep_time)

    # occassionally crashes with TwitterError, let's catch them and continue
    try:
        results = twitter_api.search(screen_name, count=50)
    except twitter.TwitterError, e:

        print e
        print 'Writing no tweets for this user...'
        users.add_user_no_tweets_found(screen_name)
        users.remove_user_not_searched(screen_name)
        return

    tw_count = 0

    Tweets = []
        
    #Name of user
    name = ""

    # note this does not guarantee we'll find one tweet per user
    for result in results:
                                
        # log of how many tweets we had to check
        tw_count += 1

        # verify tweet is from user, not directed to user
        search_result = result.AsDict()

        #Error checking to make sure everything necessary is their
        if 'user' in search_result and 'screen_name' in search_result['user'] and 'text' in search_result and 'name' in search_result['user']:

            #Make sure from correct user
            if search_result['user']['screen_name'].lower() == screen_name.lower():
                name = search_result['user']['name']

                Tweets.append(search_result['text'])

                # only write out limited number of results per user
                if tw_count >= tweets_per_user:
                    break

    #If we found tweets for user
    if len(Tweets) > 0:

        results_dict = {'Name': name, 'texts': Tweets}
        users.add_user_info(screen_name, results_dict)
        users.add_user_with_tweets(screen_name)

        #Put 5% of tweets into test database
        if random.randint(0, 20) == 1:
            users.add_user_test_sample(screen_name)

    else:
        users.add_user_no_tweets_found(screen_name)

    users.remove_user_not_searched(screen_name)


def main():

    # parameters
    num_names_to_use = 35000
    max_follower_count = 5000
    max_friend_count = 2000

    #Get terms used to identify gender
    gt = gender_terms.GenderTerms()
    male_terms = gt.get_male_terms()
    female_terms = gt.get_female_terms()

    #Twitter api client
    twitter_api = py_twitter.Twitter_Client()

    #Read and write to redis database
    users = user_database.UserDatabase()

    name_count = 0

    #While there are still users to get information about
    while len(users.get_users_not_searched()) > 0:

        male_name = GetName(male_terms, users)
        female_name = GetName(female_terms, users)

        name_count += 1

        print 'Running for names ' + male_name + ' and ' + female_name

        get_tweets(users, twitter_api, male_name, 'male')
        get_tweets(users, twitter_api, female_name, 'female')

        #Control how many names are used
        if name_count >= num_names_to_use:
            break

    f_json.close()


#Find a name to search. Look for the identifier term that currently has the least number stored
def GetName(terms, users):

    min_known_users = 1E31
    term_to_search = ""

    for term in terms:
        known_users = len(users.get_users_with_tweets_by_identifier(term))

        #If term has few known users and has names still needed to be searched for
        if known_users < min_known_users and len(users.get_users_not_searched_by_identifier(term)) > 0:

            min_known_users = known_users
            term_to_search = term

    print term_to_search

    #Return one of the users not searched from the identifier
    for user in users.get_users_not_searched_by_identifier(term_to_search):
        return user


if __name__ == '__main__':
    main()
