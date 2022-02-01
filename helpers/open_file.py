from os import path
import yaml
import json


class OpenFile:

    def __init__(self, file_path):
        self.file_path = path.abspath(file_path)
        self.allow_yaml_formats = ['yaml', 'yml']
        self.allow_json_formats = ['json']

    def check_file_exist(self):
        file_exist = path.isfile(f'{self.file_path}')
        if file_exist:
            self.open_file()
        else:
            raise FileNotFoundError

    def open_file(self):
        filename, file_extension = path.splitext(f'{self.file_path}')  # FIX
        if file_extension in self.allow_yaml_formats:
            self.open_yaml_file()
        elif file_extension in self.allow_json_formats:
            self.open_json_file()
        else:
            raise Exception(f'Format {file_extension} not supported')

    def open_yaml_file(self) -> dict:
        with open(f'{self.file_path}') as yaml_file:
            dump_yaml_file = yaml.load(yaml_file, Loader=yaml.FullLoader)
        return dump_yaml_file

    def open_json_file(self) -> dict:
        with open(f'{self.file_path}') as json_file:
            dump_json_file = json.load(json_file)
        return dump_json_file
