#Pass known email addresses to the FullContact API and retrieve any profile information

#Standard modules
import Queue
import time
import sys

#Attensity Media modules
import ContactDatabase

sys.path.append('../../social_apis/fullcontact/')
import py_fullcontact

def GetInfo(contact, ContactQueue, Contacts, fullcontact):

    # make sure we don't hit the api too much
    time.sleep(0.01)
    profile = fullcontact.searchbyemail(contact)

    status = profile['status']

    #Information successfully found                                                                                                                                            
    if status == 200:
        Contacts.add_user_info(contact, profile)
        Contacts.RemoveContactNotSearched(contact)
        Contacts.AddContactWithInfo(contact)
        AddToSets(contact, profile, Contacts)

    #Request pending, add contact to queue
    elif status == 202:
        ContactQueue.put(contact)

    #Couldn't find any information about this user
    elif status == 404:
        Contacts.RemoveContactNotSearched(contact)
        Contacts.AddContactNoInfoFound(contact)

    else:
        print "How did I get this status message " + string(status)
        

    #When we've gotten enough pending grab one of them 
    if ContactQueue.qsize()>1000:

        GetInfo(ContactQueue.get(), ContactQueue, Contacts, fullcontact)

#Add user to set defined by information returned
def AddToSets(contact, profile, Contacts):
    
    if 'socialProfiles' in profile:

        for socialProfile in profile['socialProfiles']:
            
            #Set with all users known for each social site
            Contacts.AddToSet(contact, socialProfile['typeId'])

            #Set for each facebook id known, to allow for reverse lookup
            if socialProfile['typeId'] == 'facebook':
                Contacts.AddToSet(contact, socialProfile['id'])

    if 'demographics' in profile:

        demographics = profile['demographics']

        for demographic in demographics.keys():
            Contacts.AddToSet(contact, demographic)


def main():
    
    fullcontact = py_fullcontact.FullContact_Client()

    Contacts = ContactDatabase.ContactDatabase()


    #Queue for users waiting on results for
    ContactQueue = Queue.Queue()

    #Get the info for our contacts we haven't searched
    for contact in Contacts.GetContactsNotSearched():
        
        GetInfo(contact, ContactQueue, Contacts, fullcontact)


    #Close up by finding the contacts still pending
    while ContactQueue.qsize()>0:
        GetInfo(ContactQueue.get(), ContactQueue, Contacts, fullcontact)

if __name__ == '__main__':
    main()
