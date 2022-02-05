from helpers.config_parser import ConfigParser
from helpers.http_requests import HttpRequests
from icecream import ic
import json


class Configurator:

    ic.enable()

    def __init__(self):
        self.config_parser = ConfigParser()
        self.config = self.config_parser()
        ic(self.config)

    def __call__(self):

        self.generate_result()

    def generate_result(self):
        print("Generate results")
        ic(len(self.config[0]))
        self.browser_existence_check()

    def configurate_browsers(self):
        pass

    def browser_existence_check(self):
        response = HttpRequests('hub.docker.com', '/v2/repositories/selenoid', 'page_size=50').get()
        response_body = json.loads(response.text)
        ic(response_body['count'])
        config_browser_count = len(self.config[0])
        images_count = response_body['count']
        config_browsers = []
        available_browsers = []

        for i in range(config_browser_count):
            _browser_name = self.config[0][i]['type']
            config_browsers.append(_browser_name)

        for i in range(images_count):
            _browser_name = response_body['results'][i]['name']
            available_browsers.append(_browser_name)

        ic(config_browsers)
        ic(available_browsers)
