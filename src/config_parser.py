from helpers.open_config_file import OpenFile
from pykwalify.core import Core
from icecream import ic


class ConfigParser(OpenFile):

    ic.disable()
    # ic.enable()

    def __init__(self, config_dir) -> None:
        self.config_dir = config_dir
        ic(self.config_dir)

        self.file_path = f'{self.config_dir}/config.yaml'
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
        teams = self.parse_teams_quota()

        # ic(browsers)
        # ic(aerokube)
        # ic(hosts)
        # ic(teams)
        return browsers, aerokube, hosts, teams

    def parse_browsers(self) -> dict:
        browsers = self.config_file['browsers']
        return browsers

    def parse_aerokube(self) -> dict:
        aerokube = self.config_file['aerokube']
        return aerokube

    def parse_hosts(self) -> dict:
        hosts = self.config_file['hosts']
        return hosts

    def parse_teams_quota(self) -> dict:
        try:
            teams = self.config_file['teams-quota']
        except KeyError:
            teams = {}

        return teams

    def __del__(self) -> None:
        pass
