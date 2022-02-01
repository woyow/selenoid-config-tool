from helpers.open_file import OpenFile

class ConfigParser(OpenFile):

    def __new__(cls):
        cls.file_path = './config/test_config.yaml'
        return cls

    def __init__(self):
        super().__init__(self.file_path)
        self.config_file = self.open_yaml_file()

    def __call__(self):
        valid = self.config_validation()
        if valid:
            self.config_parse()
        else:
            raise Exception

    def config_validation(self) -> bool:
        return True

    def config_parse(self):
        pass

    def parse_browsers(self):
        pass

    def parse_aerokube(self):
        pass

    def parse_teams_quota(self):
        pass

    def __del__(self):
        pass
