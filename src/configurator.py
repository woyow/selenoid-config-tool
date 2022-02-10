from helpers.config_parser import ConfigParser
from helpers.http_requests import HttpRequests
from icecream import ic
import json


class Configurator:

    # ic.disable()
    ic.enable()

    def __init__(self):
        self.config_parser = ConfigParser()
        self.config = self.config_parser()

        self.browsers = self.config[0]
        self.aerokube = self.config[1]
        self.ggr_hosts = self.config[2]
        self.selenoid_hosts = self.config[3]

        # Variables for browsers from config
        self.count_of_all_browsers = self._get_count_of_all_browsers()
        self.list_of_active_browsers = self._get_active_browsers_list()
        self.dict_of_active_browsers_versions = self._get_browsers_versions_dict()
        ic(self.dict_of_active_browsers_versions)
        # ic(self.config)

    def __call__(self):
        self.config_validation()

    def generate_result(self):
        self._browser_existence_check()

    def configurate_browsers(self):
        pass

    def config_validation(self):
        self._browser_count_check()
        self._browser_existence_check()
        self._browser_version_existence_check()

    def _browser_count_check(self):
        count = len(self.browsers)
        if count < 1:
            raise Exception('You must use at least one browser in your config')

    def _get_count_of_all_browsers(self) -> int:
        return len(self.browsers)

    def _get_active_browsers_list(self) -> list:
        browsers = []

        for i in range(self.count_of_all_browsers):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            if self.browsers[i]['use'] is True:
                # ic(self.browsers[i])
                if 'vnc-image' in browser_object and browser_object['vnc-image']['enable']:
                    vnc_browser_name = 'vnc_' + browser_name
                    browsers.append(vnc_browser_name)
                browsers.append(browser_name)

        return browsers

    def _get_browsers_versions_dict(self) -> dict:
        browsers_versions_in_config = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(len(self.list_of_active_browsers))])
        )

        for i in range(self.count_of_all_browsers):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']

            if browser_object['use']:
                if 'vnc-image' in browser_object and browser_object['vnc-image']['enable']:
                    vnc = True
                    vnc_browser_name = 'vnc_' + browser_name
                    vnc_versions = self.browsers[i]['vnc-image']['versions']
                    ic(vnc_versions)
                else:
                    vnc = None
                    vnc_browser_name = None
                    vnc_versions = None

                versions = self.browsers[i]['versions']

                if 'range' in versions:
                    _min = versions['range']['min']
                    _max = versions['range']['max']
                    if 'ignore' in versions['range']:
                        _ignore = versions['range']['ignore']
                    else:
                        _ignore = None

                    _value = _min
                    while _value != _max:
                        if _ignore:
                            if _value in _ignore:
                                _value += 1.0
                                continue
                        browsers_versions_in_config[browser_name].append(_value)
                        _value += 1.0

                elif 'array' in versions:
                    _array = versions['array']
                    for _value in _array:
                        browsers_versions_in_config[browser_name].append(_value)

                elif 'latest' in versions:
                    _value = 'latest'
                    browsers_versions_in_config[browser_name].append(_value)

                elif 'highest' in vnc_versions:
                    _value = 'highest'
                    ic(browsers_versions_in_config[browser_name][-1])

        return browsers_versions_in_config

    def _browser_existence_check(self):
        page_size_default = 25
        while True:
            response = HttpRequests(
                'hub.docker.com',
                '/v2/repositories/selenoid',
                f'page_size={page_size_default}'
            ).get()
            response_body = json.loads(response.text)

            if response_body['count'] > page_size_default:
                page_size_default = response_body['count']
            else:
                break

        images_count = response_body['count']
        available_browsers_in_registry = []

        for i in range(images_count):
            _browser_name = response_body['results'][i]['name']
            available_browsers_in_registry.append(_browser_name)

        ic(self.list_of_active_browsers)
        ic(available_browsers_in_registry)

        for i in range(len(self.list_of_active_browsers)):
            if self.list_of_active_browsers[i] in available_browsers_in_registry:
                pass
            else:
                raise Exception(
                    f'Image "{self.list_of_active_browsers[i]}" not found '
                    f'in aerokube docker registry https://hub.docker.com/u/selenoid'
                )

    def _browser_version_existence_check(self):

        available_browsers_versions_in_registry = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(len(self.list_of_active_browsers))])
        )
        ic(available_browsers_versions_in_registry)

        for browser in self.list_of_active_browsers:
            page_size_default = 25
            while True:
                response = HttpRequests(
                    'hub.docker.com',
                    f'/v2/repositories/selenoid/{browser}/tags/',
                    f'page_size={page_size_default}'
                ).get()
                response_body = json.loads(response.text)

                if response_body['count'] > page_size_default:
                    page_size_default = response_body['count']
                else:
                    break

            for i in range(response_body['count']):
                available_browsers_versions_in_registry[browser].append(response_body['results'][i]['name'])
