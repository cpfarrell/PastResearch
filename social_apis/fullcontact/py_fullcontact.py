from fullcontact import FullContact

class FullContact_Client:

    def __init__(self):

        self.fc = FullContact('ab76dbb1c4b8c50f')


    def searchbyemail(self, email):

        return self.fc.get(email=email)

