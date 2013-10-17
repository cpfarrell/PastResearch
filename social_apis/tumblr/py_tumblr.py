# py-tumblr.py
# Written by:  Alejandro Cantarero
#              alejandro.cantarero@attensitymedia.com
#
# Class and functions for accessing Tumblr via the Tumblr v2 API
#

import requests
import simplejson

class Tumblr_Client:

    # currently not using the secret key
    def __init__(self, consumer_key='r1gN36UpMIa4i3vQSOZ4SkiQe8nm6anLJGZmcFgkux24nZpgva', secret_key=None):

        self.uri = 'http://api.tumblr.com/v2/'
        
        self.query_list = {}
        self.query_list['api_key'] = consumer_key


    # search for tagged content
    #    only returns last 20 posts
    #    use time stamp as before parameter to retrieve older posts
    def tagged(self, search_tag, before=None):
        
        query = self.query_list.copy() 
        query['tag'] = search_tag

        if before is not None:
            query['before'] = before

        return requests.get(self.uri + 'tagged', params=query)


# extract the posts from a requests.Response
def extract_posts(response):

    tumblr_stream = simplejson.loads(response.__dict__['_content'])
    return tumblr_stream['response']

