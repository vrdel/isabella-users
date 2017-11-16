import os
import libuser

class UserUtils(object):
    def __init__(self, gid):
        self.gid = gid

    def create_home(self, user):
        pass

    def get_user(self, username):
        user = libuser.admin().lookupUserByName(username)

        return user
