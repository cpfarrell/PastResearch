import os
import subprocess
import redis
import ast
from collections import defaultdict

class ContactDatabase:

    def __init__(self):
        processes = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE).communicate()[0].split('\n')

        daemon_running = False
        for process in processes:
            terms = process.split()

            if len(terms) >= 5:
                if 'redis-server' in terms[4]:
                    daemon_running = True

        if not daemon_running:
            os.system('../gender/redis-2.6.14/src/redis-server ../gender/redis-2.6.14/src/redis.conf &')

        self.Database = redis.StrictRedis(host='localhost', port=6379, db=1)

    def add_user(self, Contact):

        self.Database.set(Contact, "{}")

    #Update user information, assuming passed ContactInfo. Creates user in database if not already stored.
    def add_user_info(self, Contact, ContactInfo):
        #Add user if not previously exists
        if not self.Database.exists(Contact):
            self.add_user(Contact)


        #Get info casting as dict
        info = ast.literal_eval(self.Database.get(Contact))

        info.update(ContactInfo)

        self.Database.set(Contact, info)


    #Get user info stored in databse
    def get_info(self, Contact):
        return ast.literal_eval(self.Database.get(Contact))


    def user_known(self, Contact):
        return self.Database.exists(Contact)


    #Add user as one haven't looked for info from
    def AddContactNotSearched(self, Contact):
        self.Database.sadd("ContactsNotSearched", Contact)


    #Return all users. Slow, use judiciously!
    def GetAllContacts(self):
        return self.Database.sunion("ContactsNotSearched", "ContactsWithInfo", "ContactsNoInfoFound")

    #Get List of Contacts That Haven't Tried To Find Info From
    def GetContactsNotSearched(self):
        return self.Database.smembers("ContactsNotSearched")

    #Remove user from set of users not searched
    def RemoveContactNotSearched(self, Contact):
        self.Database.srem("ContactsNotSearched", Contact)

    #Add user to set of those with info
    def AddContactWithInfo(self, Contact):
        self.Database.sadd("ContactsWithInfo", Contact)

    #Get all users with info
    def GetContactsWithInfo(self):
        return self.Database.smembers("ContactsWithInfo")

    #Check if have info on user
    def ContactHasInfo(self, Contact):
        if self.user_known(Contact):
            return True

        else:
            return False

    #Add user to set of those no info found for when searched
    def AddContactNoInfoFound(self,Contact):
        self.Database.sadd("ContactsNoInfoFound", Contact)

    #Get all users not able to find info from
    def GetContactsNoInfoFound(self):
        return self.Database.smembers("ContactsNoInfoFound")


    def AddToSet(self, Contact, setName):
        self.Database.sadd(setName, Contact)

    def GetSetContacts(self, setName):
        return self.Database.smembers(setName)


    def AddMovie(self, Contact, movie):
        
        Info = self.get_info(Contact)

        if Movies in Info:

            Movies = Info["Movies"]
            Movies.append(movie)

        else:
            Movies = [movie]

        add_user_info(self, Contact, {"Movies": Movies})

    #Assumes ID known
    def GetSocialID(self, Contact, site):

        profile = self.get_info(Contact)

        for socialProfile in profile['socialProfiles']:
        
            if socialProfile['typeId'] == site:
                return socialProfile['id']
