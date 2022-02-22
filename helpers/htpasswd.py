import htpasswd
from helpers.file_system import FileSystem

class Htpasswd:

    def __init__(self, path: str, file_name: str, name: str, password: str) -> None:
        self.dir_name = dir_name
        self.file_name = file_name
        self.name = name
        self.password = password
        self.full_path = self.path + '/' + self.file_name

    def add_user(self):
        FileSystem(
            self.dir_name,
            self.file_name
        ).create_file()

        with htpasswd.Basic(self.full_path) as users_db:
            try:
                users_db.add(self.name, self.password)
            except htpasswd.basic.UserExists:
                pass
