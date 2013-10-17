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

sys.path.append('../../social_apis/twitter/')

# non-standard modules
import simplejson
import twitter

# attensity media modules
import demographics
import py_twitter
sys.path.append('../UserDatabase/')
import user_database


def main():

    # parameters
    num_names_to_use = 300
    num_users_per_name = 52  # number of different user accounts to use per name
    tweets_per_user = 15
    initial_page = 20
    twitter_api_sleep_time = 10
    count = 100
    max_follower_count = 5000
    max_friend_count = 2000

    #Put output in redis database
    user_db = user_database.UserDatabase()

    (male_names, female_names) = demographics.find_top_non_repeated_names(num_names_to_use)
    twitter_api = py_twitter.Twitter_Client()

    for male_name, female_name in itertools.izip_longest(male_names, female_names):

        name_count = 0

        for name, gender in itertools.izip((male_name, female_name), ("male", "female")):

            #Name can be none if one of the name lists is longer than the other
            if name is None:
                continue
            
            page = initial_page
            account_found = False

            out_string = 'Processing name ' + str(name) + ' (count = ' + str(name_count) + ').'
            name_count += 1
            sys.stdout.write(out_string)

            #while not account_found:
            while len(user_db.get_users_by_identifier("PersonIdentifiedByFirstName_" + name.lower())) < num_users_per_name:

                user_search_count = 0                

                # make sure we don't hit the api too much
                time.sleep(twitter_api_sleep_time)
                users = twitter_api.search_user_names(name, page=page, count=count)

                #Continue if get back error, can happen if page is beyond the number of pages with results
                if 'errors' in users:
                    break
                
                for user in users:

                    # log of how many users we had to check
                    user_search_count += 1

                    screen_name = user['screen_name']

                    #Make sure can find a first time
                    if len(user['name'].split()) == 0:
                        continue

                    # only take users using english as their primary language
                    # check that name is a first name, do not want to match last names
                    if user['lang'] == 'en' and user['name'].split()[0].lower() == name.lower():

                        # attempt to weed out businesses and celebrities
                        if user['followers_count'] < max_follower_count and user['friends_count'] < max_friend_count:

                            #Don't look for users with tweets already stored but record that they were identified by first name
                            if user_db.user_has_tweets(screen_name):

                                user_db.add_user_identifier("PersonIdentifiedByFirstName_" + name.lower(), screen_name)
                                user_db.add_user_identifier("FirstName", screen_name)
                                user_db.add_user_identifier("GenderKnown", screen_name)
                                continue
                            
                            # account found, pull a post
                            #  careful about api limits
                            time.sleep(twitter_api_sleep_time)

                            # occassionally crashes with TwitterError, let's catch them and continue
                            try:
                                results = twitter_api.search(user['screen_name'], count=50)
                            except twitter.TwitterError, e:

                                print e
                                print 'Continuing...'
                                continue

                            tw_count = 0
                            Tweets = []
                            
                            # note this does not guarantee we'll find one tweet per user
                            for result in results:
                                
                                # log of how many tweets we had to check
                                tw_count += 1

                                # verify tweet is from user, not directed to user
                                search_result = result.AsDict()
                                if search_result['user']['screen_name'] == screen_name:

                                    Tweets.append(search_result['text'])

                                    if len(Tweets) > tweets_per_user:
                                        break

                            #Don't use users we didn't find any tweets from
                            if len(Tweets) == 0:
                                continue

                            #Add user to database with meta data
                            results_dict = {'Gender': gender, 'Name': user['name'], 'texts': Tweets}
                            user_db.add_user_info(screen_name, results_dict)

                            user_db.add_user_identifier("PersonIdentifiedByFirstName_" + name.lower(), screen_name)
                            user_db.add_user_identifier("FirstName", screen_name)
                            user_db.add_user_with_tweets(screen_name)

                            #Put 5% of tweets into test database
                            if random.randint(0, 20) == 1:
                                user_db.add_user_test_sample(screen_name)

                            out_string = '(u-' + str(user_search_count) + ', t-' + str(tw_count) + ')'
                            sys.stdout.write(out_string + '\n')


                # did not find a user?  keep searching
                page += 1



if __name__ == '__main__':
    main()
