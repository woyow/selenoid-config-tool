from helpers.open_file import OpenFile
from pykwalify.core import Core
from icecream import ic


class ConfigParser(OpenFile):

    ic.disable()
    # ic.enable()

    def __init__(self) -> None:
        self.file_path = './config/test_config.yaml'
        self.schema_path = './config/schema/config_schema.yaml'
        super().__init__(self.file_path)
        self.config_file = self.open_yaml_file()

    def __call__(self) -> tuple:
        is_config_valid = self.config_validation()
        # ic(is_config_valid)
        if is_config_valid:
            parsed_config = self.config_parse()
        else:
            raise Exception

        return parsed_config

    def config_validation(self) -> bool:
        c = Core(source_file=self.file_path, schema_files=[self.schema_path])
        c.validate(raise_exception=True)
        return True

    def config_parse(self) -> tuple:
        browsers = self.parse_browsers()
        aerokube = self.parse_aerokube()
        hosts = self.parse_hosts()

        # ic(browsers)
        # ic(aerokube)
        # ic(hosts)
        return browsers, aerokube, hosts

    def parse_browsers(self):
        browsers = self.config_file['browsers']
        return browsers

    def parse_aerokube(self):
        aerokube = self.config_file['aerokube']
        return aerokube

    def parse_hosts(self):
        hosts = self.config_file['hosts']
        return hosts

    def __del__(self):
        pass
