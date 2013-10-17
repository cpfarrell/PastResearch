#py_facebook.py
#Written by Chris Farrell starting on 08 Aug 2013
#farrell.chris1@gmail.com
#
#Pull down information from Facebook

import facebook

#Simple code that just stores access token so that it doesn't need to be uploaded to github
#Need to make this file and get your access token
import access_token

class Facebook_Client:

    def __init__(self):

        self.graph = facebook.GraphAPI(access_token.access_token)


    #Search facebook for the given query and return the specified type (post, user,..)
    def search(self, query, type):

        return self.graph.request("search", {"q": query, "type": type})


    def request(self, query, PrevPage = None):
        args = {}

        if PrevPage:

            if 'paging' in PrevPage and 'next' in PrevPage['paging']:
                
                if 'cursors' in PrevPage['paging']:
                    args['after'] = PrevPage['paging']['cursors']['after']
        
                else:
                    NextUrl = PrevPage['paging']['next']
                    Start = NextUrl.find('until') + 6
                    
                    if Start == -1:
                        return None

                    End = NextUrl.find('&', Start) - 1
                    
                    if End < 0:
                        End = len(NextUrl)

                    print NextUrl
                    args['until'] = NextUrl[Start:End]

            else:
                return None

        return self.graph.request(query, args)

