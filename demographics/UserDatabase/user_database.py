import os
import subprocess
import redis
import ast
import random
from collections import defaultdict

class UserDatabase:
    def __init__(self):
        processes = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE).communicate()[0].split('\n')

        daemon_running = False
        for process in processes:
            terms = process.split()

            if len(terms) >= 5:
                if 'redis-server' in terms[4]:
                    daemon_running = True

        if not daemon_running:
            #Path needs to be set depending on where running from
            #path = '/home/dev/redis-2.6.14/src/'
            path = '/Users/chrisfarrell/Work/attensitymedia/Research/demographics/UserDatabase/redis-2.6.14/src/'
            os.system(path + 'redis-server ' + path + 'redis.conf &')

        self.database = redis.StrictRedis(host='localhost', port=6379, db=0)

    def add_user(self, user):
        self.database.set(user, "{}")

    #Update user information, assuming passed UserInfo. Creates user in database if not already stored.
    def add_user_info(self, user, user_info):
        #Add user if not previously exists
        if not self.database.exists(user):
            self.add_user(user)

        #Get info casting as dict
        info = ast.literal_eval(self.database.get(user))
        info.update(user_info)
        self.database.set(user, info)
        
    #Get user info stored in databse
    def get_info(self, user):
        return ast.literal_eval(self.database.get(user))

    def user_known(self, user):
        return self.database.exists(user)

    #Add user as one haven't looked for tweets from
    def add_user_not_searched(self, user):
        self.database.sadd("UsersNotSearched", user)

    #Return all users. Slow, use judiciously!
    def get_all_users(self):
        return self.database.sunion("UsersNotSearched", "UsersWithTweets", "UsersNoTweetsFound")

    #Get List of Users That Haven't Tried To Find Tweets From
    def get_users_not_searched(self):
        return self.database.smembers("UsersNotSearched")

    #Get List of Users That Haven't Tried To Find Tweets From by identifier
    def get_users_not_searched_by_identifier(self, identifier):
        return self.database.sinter("UsersNotSearched", identifier)

    #Remove user from set of users not searched
    def remove_user_not_searched(self, user):
        self.database.srem("UsersNotSearched", user)

    #Add user as having been identified in some manner. Note if user identified twice by different identifiers will be in both sets
    def add_user_identifier(self, identifier, user):
        self.database.sadd(identifier, user)

    #Get users identified in some manner
    def get_users_by_identifier(self, identifier):
        return self.database.smembers(identifier)


    #Add user to set of those with tweets
    def add_user_with_tweets(self, user):
        self.database.sadd("UsersWithTweets", user)

    #Get all users with tweets
    def get_users_with_tweets(self):
        return self.database.smembers("UsersWithTweets")

    #Get random users with tweets
    def get_random_users_with_tweets(self, count = 1):
        return self.database.srandmember("UsersWithTweets", count)

    #Check if user in test sample
    def user_in_test_sample(self, user):
        return self.database.sismember("UsersTestSample", user)

    #Add user to test sample
    def add_user_test_sample(self, user):
        return self.database.sadd("UsersTestSample", user)

    #Get all users with tweets
    def get_users_with_tweets_by_identifier(self, identifier):
        return self.database.sinter("UsersWithTweets", identifier)

    def user_known_by_identifier(self, identifier, user):
        return self.database.sismember(identifier, user)

    #Check if have tweets on user
    def user_has_tweets(self, user):
        if self.user_known(user):
            return True
        else:
            return False

    #Add user to set of those no tweets found for when searched
    def add_user_no_tweets_found(self,user):
        self.database.sadd("UsersNoTweetsFound", user)

    #Get all users not able to find tweets from
    def get_users_no_tweets_found(self):
        return self.database.smembers("UsersNoTweetsFound")

    #Assumes gender is already stored
    def get_user_gender(self, user):
        return ast.literal_eval(self.database.get(user))["Gender"]

