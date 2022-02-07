from helpers.config_parser import ConfigParser
from helpers.http_requests import HttpRequests
from icecream import ic
import json


class Configurator:

    #ic.disable()
    ic.enable()

    def __init__(self):
        self.config_parser = ConfigParser()
        self.config = self.config_parser()

        self.browsers = self.config[0]
        self.aerokube = self.config[1]
        self.ggr_hosts = self.config[2]
        self.selenoid_hosts = self.config[3]

        # Variables for browsers
        self.count_of_all_browsers = self._get_count_of_all_browsers()
        self.list_of_active_browsers = self._get_active_browsers_list()
        ic(self.config)

    def __call__(self):
        self.config_validation()

    def generate_result(self):
        print("Generate results")
        ic(len(self.browsers))
        self.browser_existence_check()

    def configurate_browsers(self):
        pass

    def config_validation(self):
        self.browser_count_check()
        self.browser_existence_check()
        self.browser_version_existence_check()

    def browser_count_check(self):
        count = len(self.browsers)
        if count < 1:
            raise Exception('You must use at least one browser in your config')

    def _get_count_of_all_browsers(self) -> int:
        return len(self.browsers)

    def _get_active_browsers_list(self) -> list:
        browsers = []

        for i in range(self.count_of_browsers):
            _browser_name = self.browsers[i]['type']
            if self.browsers[i]['use'] is True:
                ic(self.browsers[i])
                if 'vnc-image' in self.browsers[i] and self.browsers[i]['vnc-image']['enable']:
                    _browser_name = 'vnc_' + _browser_name
                browsers.append(_browser_name)

        return browsers


    def browser_existence_check(self):
        page_size_default = 25
        while True:
            response = HttpRequests('hub.docker.com', '/v2/repositories/selenoid', f'page_size={page_size_default}').get()
            response_body = json.loads(response.text)
            ic(response_body['count'])
            if response_body['count'] > page_size_default:
                page_size_default = response_body['count']
            else:
                break

        config_browsers_count = len(self.browsers)
        images_count = response_body['count']
        config_browsers = []
        available_browsers = []

        for i in range(config_browsers_count):
            _browser_name = self.browsers[i]['type']
            if self.browsers[i]['use'] is True:
                ic(self.browsers[i])
                if 'vnc-image' in self.browsers[i] and self.browsers[i]['vnc-image']['enable']:
                    _browser_name = 'vnc_' + _browser_name
                config_browsers.append(_browser_name)
            else:
                config_browsers_count -= 1

        for i in range(images_count):
            _browser_name = response_body['results'][i]['name']
            available_browsers.append(_browser_name)

        ic(config_browsers)
        ic(available_browsers)

        for i in range(config_browsers_count):
            if config_browsers[i] in available_browsers:
                pass
            else:
                raise Exception(
                    f'Image "{config_browsers[i]}" not found in aerokube docker registry https://hub.docker.com/u/selenoid'
                )

    def browser_version_existence_check(self):
        page_size_default = 25
        while True:
            'https://hub.docker.com/v2/repositories/selenoid/chrome/tags/?page_size=51'
            response = HttpRequests('hub.docker.com', '/v2/repositories/selenoid/chrome/tags/', f'page_size={page_size_default}')
            response_body = json.loads(response.text)
            ic(response_body['count'])
            if response_body['count'] > page_size_default:
                page_size_default = response_body['count']
            else:
                break
