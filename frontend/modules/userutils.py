import libuser

class UserUtils(object):
    def __init__(self, logger, home_prefix='/home'):
        self.logger = logger
        self.home_prefix = home_prefix

    def get_user(self, username):
        user = libuser.admin().lookupUserByName(username)
        return user

    def all_users_list(self):
        users = libuser.admin().enumerateUsersFull()
        users = [u for u in users if self.get_user_home(u).startswith('/home')]
        users = [self.get_user_name(u) for u in users]
        return users

    def all_users(self):
        users = libuser.admin().enumerateUsersFull()
        users = [u for u in users if self.get_user_home(u).startswith('/home')]
        return users

    def info_comment(self, userobj):
        comment = self.get_user_comment(userobj)
        name, surname, project = '', '', ''
        if comment:
            if ',' in comment:
                fullname, project = map(lambda x: x.strip(), comment.split(','))
                name, surname = fullname.split(' ')
            else:
                name, surname = comment.split(' ')

        return name, surname, project

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
