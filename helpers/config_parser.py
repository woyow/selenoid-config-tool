from helpers.open_file import OpenFile
from pykwalify.core import Core
from icecream import ic


class ConfigParser(OpenFile):

    #ic.disable()

    def __init__(self) -> None:
        self.file_path = './config/test_config.yaml'
        self.schema_path = './config/schema/config_schema.yaml'
        super().__init__(self.file_path)
        self.config_file = self.open_yaml_file()
        ic(self)

    def __call__(self) -> None:
        print("CALL CONFIG PARSER")
        valid = self.config_validation()
        ic(valid)
        #if valid:
        #    self.config_parse()
        #else:
        #    raise Exception

    def config_validation(self) -> bool:
        c = Core(source_file=self.file_path, schema_files=[self.schema_path])
        c.validate(raise_exception=True)
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