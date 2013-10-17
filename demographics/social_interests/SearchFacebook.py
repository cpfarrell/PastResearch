#Pass known email addresses to the FullContact API and retrieve any profile information

#Standard modules
import sys
import time

#Attensity Media modules
import ContactDatabase
sys.path.append('../../social_apis/facebook/')
import py_facebook



def main():    
    contacts = ContactDatabase.ContactDatabase()
    facebook_client = py_facebook.Facebook_Client()
    sleep_time = 0.2

    movies = [
        ("getaway", "466294513405510"),
        ("the family", "131450793725696"),
        ("we're the millers", "220220544708630")
        ]


    for movie in movies:
        #Make sure we don't hit the API too much
        time.sleep(sleep_time)

        pageposts = facebook_client.request(movie[1] + '/posts') 
        while pageposts:
            for post in pageposts['data']:
                if 'likes' not in post:
                    continue

                likes = post['likes']
                postid = post['id']

                while likes:                    
                    for user in likes['data']:
                        user_id = user['id']

                        for contact in contacts.GetSetContacts(user_id):
                            contacts.AddMovie(contact, movie)

                    #Make sure we don't hit the API too much 
                    time.sleep(sleep_time)
                    likes = facebook_client.request(postid + '/likes', likes)
                        
            pageposts = facebook_client.request(ID + '/posts', pageposts)

    
if __name__ == '__main__':
    main()
