from helpers.open_file import OpenFile
from pykwalify.core import Core
#import cerberus


class ConfigParser(OpenFile):

    def __new__(cls) -> object:
        cls.file_path = './config/test_config.yaml'
        cls.schema_path = './config/schema/config_schema.yaml'
        return cls

    def __init__(self) -> None:
        super().__init__(self.file_path)
        self.config_file = self.open_yaml_file()

    def __call__(self) -> None:
        valid = self.config_validation()
        if valid:
            self.config_parse()
        else:
            raise Exception

    def config_validation(self) -> bool:
        try:
            c = Core(source_file=self.file_path, schema_files=[self.schema_path])
            c.validate(raise_exception=True)
            return True
        except:
            return False


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
