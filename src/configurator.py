from helpers.config_parser import ConfigParser
from helpers.http_requests import HttpRequests
from icecream import ic
import json


def _docker_hub_get_request(
        domain: str = None,
        method: str = None,
        params: dict = None,
        headers: dict = None,
        body: dict = None,
        secure: bool = None,
        check_count: bool = None
):
    while True:
        response = HttpRequests(
            domain,
            method,
            params,
            headers,
            body,
            secure
        ).get()

        response_body = json.loads(response.text)
        if check_count is not False:
            if response_body['count'] > params['page_size']:
                params['page_size'] = response_body['count']
            else:
                break
        else:
            break

    return response_body


def _range_handler(versions: dict, target_array: list):
    min_version = versions['range']['min']
    max_version = versions['range']['max']
    if 'ignore' in versions['range']:
        ignore = versions['range']['ignore']
    else:
        ignore = None

    value = min_version
    while value != max_version:
        if ignore:
            if value in ignore:
                value += 1.0
                continue
        target_array.append(value)
        value += 1.0


def _array_handler(browser_name: str, versions: dict, target_array: list):
    array = versions['array']
    for value in array:
        if value == 'latest':
            _latest_handler(browser_name, target_array)
        else:
            target_array.append(value)

    target_array = list(set(target_array))


def _latest_handler(browser_name: str, target_array: list):
    page_size_default = 2
    response_body = _docker_hub_get_request(
        'hub.docker.com',
        f'/v2/repositories/selenoid/{browser_name}/tags/',
        {'page_size': page_size_default},
        check_count=False
    )

    results = response_body['results']
    if len(results) > 1:
        if results[0]['name'] == 'latest':
            value = results[1]['name']
        else:
            value = results[0]['name']
    else:
        value = results[0]['name']
    ic(browser_name, value, "latest_handler")
    target_array.append(float(value))


def _highest_handler(source_array: list, target_array: list):
    value = source_array[-1]
    target_array.append(value)


def _validation_boundary_conditions(browser_name: str, source_array: list, target_array: list):
    """
    browser_name - basic browser name
    source_array - array with vnc_browsers
    target_array - array with browsers
    """

    # ic(browser_name)
    # ic(target_array)
    # ic(source_array)

    # ic(len(source_array))
    # ic(len(target_array))
    min_a = min(source_array)
    min_b = min(target_array)
    max_a = max(source_array)
    max_b = max(target_array)

    if min_a < min_b:
        raise Exception(
            'VNC version less then browser version; '
            f'vnc_{browser_name} version: {min_a}; {browser_name} version: {min_b}!'
        )
    if max(source_array) > max(target_array):
        raise Exception(
            'VNC version is greater then browser version; '
            f'vnc_{browser_name} version: {max_a}; {browser_name} version: {max_b}!'
        )


def _remove_same_values_from_array(source_array: list, target_array: list):
    for version in source_array:
        try:
            target_array.remove(version)
        except ValueError:
            continue


def _get_vnc_params(browser, browser_name) -> (bool, str, dict, dict) or (None, None, None, None):
    """
    browser - dict with browser object
    browser_name - string with basic browser name
    """
    if 'vnc-image' in browser and browser['vnc-image']['enable']:
        vnc = True
        vnc_browser_name = 'vnc_' + browser_name
        vnc_versions = browser['vnc-image']['versions']
        vnc_default_version_object = browser['vnc-image']['default-version']
    else:
        vnc = None
        vnc_browser_name = None
        vnc_versions = None
        vnc_default_version_object = None

    return vnc, vnc_browser_name, vnc_versions, vnc_default_version_object


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
        self.dict_of_default_browser_version = self._get_default_browser_version_dict()
        ic(self.dict_of_active_browsers_versions)
        ic(self.dict_of_default_browser_version)
        # ic(self.config)

    def __call__(self):
        self.config_validation()

    def generate_result(self):
        self._browser_existence_check()

    def configurate_browsers(self):
        pass

    def config_validation(self):
        self._browser_count_check()
        self._browser_existence_in_registry_check()
        self._browser_version_existence_in_registry_check()

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
                vnc, vnc_browser_name, _, _ = _get_vnc_params(browser_object, browser_name)
                if vnc:
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
                vnc, vnc_browser_name, vnc_versions, _ = _get_vnc_params(browser_object, browser_name)

                versions = self.browsers[i]['versions']

                if 'range' in versions:
                    _range_handler(versions, browsers_versions_in_config[browser_name])

                elif 'array' in versions:
                    _array_handler(browser_name, versions, browsers_versions_in_config[browser_name])

                elif 'latest' in versions:
                    _latest_handler(browser_name, browsers_versions_in_config[browser_name])

                if vnc:
                    if 'range' in vnc_versions:
                        _range_handler(vnc_versions, browsers_versions_in_config[vnc_browser_name])

                    elif 'array' in vnc_versions:
                        _array_handler(browser_name, vnc_versions, browsers_versions_in_config[vnc_browser_name])

                    elif 'latest' in vnc_versions:
                        _latest_handler(vnc_browser_name, browsers_versions_in_config[vnc_browser_name])

                    elif 'highest' in vnc_versions:
                        _highest_handler(
                            browsers_versions_in_config[browser_name],
                            browsers_versions_in_config[vnc_browser_name]
                        )

                    _validation_boundary_conditions(
                        browser_name,
                        browsers_versions_in_config[vnc_browser_name],
                        browsers_versions_in_config[browser_name]
                    )

                    _remove_same_values_from_array(
                        browsers_versions_in_config[vnc_browser_name],
                        browsers_versions_in_config[browser_name]
                    )

                    if len(browsers_versions_in_config[browser_name]) < 1:
                        browsers_versions_in_config.pop(browser_name)

        return browsers_versions_in_config

    def _get_default_browser_version_dict(self) -> dict:

        default_browser_version_in_config = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(len(self.list_of_active_browsers))])
        )

        for i in range(len(self.browsers)):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            vnc, vnc_browser_name, vnc_versions, vnc_default_version_object = _get_vnc_params(
                browser_object, browser_name
            )
            default_version_object = browser_object['default-version']

            if browser_name in self.dict_of_active_browsers_versions:
                vnc_only = None
            else:
                vnc_only = True
                default_browser_version_in_config.pop(browser_name)

            ic(self.dict_of_active_browsers_versions)
            if not vnc_only:
                versions_list = self.dict_of_active_browsers_versions[browser_name]
                ic(versions_list)

                if 'custom' in default_version_object:
                    value = default_version_object['custom']
                elif 'highest' in default_version_object:
                    value = max(self.dict_of_active_browsers_versions[browser_name])
                elif 'minimal' in default_version_object:
                    value = min(self.dict_of_active_browsers_versions[browser_name])

                default_browser_version_in_config[browser_name].append(value)

            if vnc:
                vnc_versions_list = self.dict_of_active_browsers_versions[vnc_browser_name]
                ic(vnc_versions_list)

                if 'custom' in vnc_default_version_object:
                    value = vnc_default_version_object['custom']
                elif 'highest' in vnc_default_version_object:
                    value = max(self.dict_of_active_browsers_versions[vnc_browser_name])
                elif 'minimal' in vnc_default_version_object:
                    value = min(self.dict_of_active_browsers_versions[vnc_browser_name])

                default_browser_version_in_config[vnc_browser_name].append(value)

        return default_browser_version_in_config

    def _browser_existence_in_registry_check(self):
        page_size_default = 25
        response_body = _docker_hub_get_request(
            'hub.docker.com',
            '/v2/repositories/selenoid',
            {'page_size': page_size_default}
        )

        images_count = response_body['count']
        available_browsers_in_registry = []

        for i in range(images_count):
            _browser_name = response_body['results'][i]['name']
            available_browsers_in_registry.append(_browser_name)

        #ic(self.list_of_active_browsers)
        #ic(available_browsers_in_registry)

        for i in range(len(self.list_of_active_browsers)):
            if self.list_of_active_browsers[i] in available_browsers_in_registry:
                pass
            else:
                raise Exception(
                    f'Image "{self.list_of_active_browsers[i]}" not found '
                    f'in aerokube docker registry https://hub.docker.com/u/selenoid'
                )

    def _docker_hub_request(*request_payload):
        ic(request_payload)
        while True:
            response = HttpRequests(request_payload).get()
            response_body = json.loads(response.text)

            if response_body['count'] > page_size_default:
                page_size_default = response_body['count']
            else:
                break

    def _browser_version_existence_in_registry_check(self):

        available_browsers_versions_in_registry = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(len(self.list_of_active_browsers))])
        )

        for browser in self.list_of_active_browsers:
            page_size_default = 25
            response_body = _docker_hub_get_request(
                'hub.docker.com',
                f'/v2/repositories/selenoid/{browser}/tags/',
                {'page_size': page_size_default}
            )

            for i in range(response_body['count']):
                available_browsers_versions_in_registry[browser].append(response_body['results'][i]['name'])

            # ic(available_browsers_versions_in_registry[browser])

            temp_versions_list = self.dict_of_active_browsers_versions[browser] #  TODO: exclude vnc_only browser
            # ic(temp_versions_list)
            # ic(type(temp_versions_list))
            for i in range(len(temp_versions_list)):
                if str(temp_versions_list[i]) in available_browsers_versions_in_registry[browser]:
                    # ic(browser, temp_versions_list[i], "OK")
                    pass
                else:
                    raise Exception(
                        f'{browser}:{temp_versions_list[i]} not found into selenoid docker registry. '
                        f'Available versions: {available_browsers_versions_in_registry[browser]}'
                    )
        #ic(available_browsers_versions_in_registry)
