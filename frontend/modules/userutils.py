import libuser

class UserUtils(object):
    def __init__(self, logger):
        self.logger = logger

    def get_user(self, username):
        user = libuser.admin().lookupUserByName(username)
        return user

    def get_user_home(self, userobj):
        return userobj.get(libuser.HOMEDIRECTORY)[0]

    def get_user_id(self, userobj):
        return userobj.get(libuser.UIDNUMBER)[0]

    def get_user_pass(self, userobj):
        return userobj.get(libuser.SHADOWPASSWORD)[0]

    def set_user_pass(self, userobj, password):
        libuser.admin().setpassUser(userobj, password, False)
