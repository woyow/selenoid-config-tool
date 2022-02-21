import os
from pathlib import Path
import shutil


class FileSystem:

    def __init__(self, dir_name: str = None, file_name: str = None) -> None:
        if dir_name:
            self.dir_name = dir_name
            self.path = self.dir_name
        elif file_name:
            self.dir_name = './'
            self.file_name = file_name
            self.path = self.dir_name + self.file_name

    def create_dir(self) -> None:
        Path(self.path).mkdir(parents=True, exist_ok=True)

    def create_file(self) -> None:
        with open(self.path, mode='a'):
            pass

    def remove_dir(self) -> None:
        try:
            shutil.rmtree(self.path)  # recursive remove dirs
        except FileNotFoundError:
            pass

    def remove_file(self):
        pass

    def is_dir_exist(self) -> bool:
        is_dir_exist = os.path.isdir(self.path)
        return is_dir_exist

    def is_file_exist(self) -> bool:
        is_file_exist = os.path.isfile(self.path)
        return is_file_exist

    def get_dir_listing(self) -> list:
        dir_listing = os.listdir(self.path)
        return dir_listing
