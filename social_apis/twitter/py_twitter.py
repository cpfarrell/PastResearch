# py_twitter.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# Routines to start pulling demographic information on users
#

import requests
import twitter
import os
import sys

from requests_oauthlib import OAuth1
            

class Twitter_Client:

    def __init__(self):

        # OAuth keys for AM Pipeline project

        if 'farrell' in os.getcwd():
            self.access_token_key = "1586348324-jvzWKa7kqKNXX7ReIkGde3jRzCdx5xjp68cJq7T"
            self.access_token_secret = "qnQ7J7sPLD4Ytzhn97T2d7ByoXuXzffYMaw4Rnfe5eM"
            self.consumer_key = "4jWCIgTdGs6aGfSJs7JQFQ"
            self.consumer_secret = "01vpjOfCLsow6iVhF6w2WKBsP9A1LeXWfYJOf8ozuao"

        else:
            self.access_token_key = "1187799457-16qyxpeILWjJRc5FVWZQHo6VTh9KIEYymmA7NTW"
            self.access_token_secret = "ynGbIaoDL5cC7DjfMyVCa3Ql9H4IQrr6MXYJWzCRc"
            self.consumer_key = "iVKckfm2zUekBvo9IWXKPA"
            self.consumer_secret = "OlzYsXLWf43H5PhIfkDltMwed26YZska87hZ62VJo"

        self.api = twitter.Api(consumer_key=self.consumer_key,
                  consumer_secret=self.consumer_secret,
                  access_token_key=self.access_token_key,
                  access_token_secret=self.access_token_secret,
                  cache=None)


    def search(self, query, count=15, until="", since_id=0, max_id=sys.maxint):

        return self.api.GetSearch(term=query, count=count, until=until, lang="en", since_id=since_id, max_id=max_id)

    #Get friends will exceed rate limit if more than 300 friends
    def get_friends(self):

        return self.api.GetFriends()

    #Returns just the ID of users that are following
    def get_friend_ids(self):

        return self.api.GetFriendIDs()

    def get_user_from_id(self, user_id):

        return self.api.UsersLookup(user_id = user_id)

    def get_profiles_from_search_results(self, twitter_statuses):

        screen_names = [status.GetUser().screen_name for status in twitter_statuses]
        return self.api.UsersLookup(screen_name = screen_names)


    # search for a user who's name contains search_string.  includes name, screen_name,
    #    description, url, etc.
    def search_user_names(self, search_string, count=20, page=1):

        api_uri = 'https://api.twitter.com/1.1/users/search.json'

        oauth = OAuth1(self.consumer_key,
                       client_secret=self.consumer_secret,
                       resource_owner_key=self.access_token_key,
                       resource_owner_secret=self.access_token_secret)

        params = {'q':search_string, 'page': page, 'count': count}
        r = requests.get(url=api_uri, auth=oauth, params=params)

        return r.json()

