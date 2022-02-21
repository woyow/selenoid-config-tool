import htpasswd


class Htpasswd:

    def __init__(self, path: str, user: str, password: str) -> None:
        self.path = path
        self.user = user
        self.password = password
        self.file_name = 'users.htpasswd'
        self.full_path = self.path + '' + self.file_name

    def add_user(self):
        with htpasswd.Basic(self.full_path) as users_db:
            try:
                users_db.add(self.user, self.password)
            except htpasswd.basic.UserExists:
                pass
