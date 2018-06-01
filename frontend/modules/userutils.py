import libuser

class UserUtils(object):
    def __init__(self, logger):
        self.logger = logger

    def get_user(self, username):
        user = libuser.admin().lookupUserByName(username)
        return user

    def all_users(self):
        users = libuser.admin().enumerateUsersFull()
        return users

    def get_user_home(self, userobj):
        return userobj.get(libuser.HOMEDIRECTORY)[0]

    def get_user_name(self, userobj):
        return userobj.get(libuser.USERNAME)[0]

    def get_user_id(self, userobj):
        return userobj.get(libuser.UIDNUMBER)[0]

    def get_user_pass(self, userobj):
        return userobj.get(libuser.SHADOWPASSWORD)[0]

    def get_user_comment(self, userobj):
        return userobj.get(libuser.GECOS)[0]

    def set_user_pass(self, userobj, password):
        libuser.admin().setpassUser(userobj, password, False)

    def get_user_shell(self, userobj):
        return userobj.get(libuser.LOGINSHELL)[0]
