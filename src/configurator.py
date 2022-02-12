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
    """ Wrapper for convenient queries to the docker registry """

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


def _range_handler(browser_name: str, versions: dict, target_array: list):
    """ 'range' key handler from config """
    min_version = versions['range']['min']
    max_version = versions['range']['max']
    # ic(min_version)
    # ic(max_version)

    if max_version == 'latest':
        max_version = _latest_handler(browser_name, target_array, return_value=True)
        # ic(max_version)

    if 'ignore' in versions['range']:
        ignore = versions['range']['ignore']
    else:
        ignore = None

    value = min_version
    while value <= max_version:
        if ignore:
            if value in ignore:
                value += 1.0
                continue
        target_array.append(value)
        value += 1.0


def _array_handler(browser_name: str, versions: dict, target_array: list):
    """ 'array' key handler from config """
    array = versions['array']
    for value in array:
        if value == 'latest':
            _latest_handler(browser_name, target_array)
        else:
            target_array.append(value)

    array_without_same_values = list(set(target_array))  # CASE: latest_version=100, array: [100, latest]
    target_array.clear()
    target_array.extend(array_without_same_values)


def _latest_handler(browser_name: str, target_array: list, return_value: bool = None) -> float or None:
    """ 'latest' key handler from config """
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
    # ic(browser_name, value, "latest_handler")

    if return_value:
        return float(value)
    else:
        target_array.append(float(value))


def _highest_handler(source_array: list, target_array: list) -> None:
    """ 'highest' key handler from config """
    value = source_array[-1]
    target_array.append(value)


def _validation_boundary_conditions(browser_name: str, source_array: list, target_array: list):
    """
    Checking that the source_array has not gone beyond the target_array

    browser_name - basic browser name
    source_array - array with vnc_browsers
    target_array - array with browsers
    """

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


def _remove_same_values_from_array(source_array: list, target_array: list) -> None:
    """ Removing duplicate values from source_array in the target_array """
    for version in source_array:
        try:
            target_array.remove(version)
        except ValueError:
            continue


def _get_vnc_params(browser: dict, browser_name: str) -> (bool, str, dict, dict) or (None, None, None, None):
    """
    Getting the values you need to work with VNC browsers from config

    browser - browser object
    browser_name - string with browser name (not vnc)
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


def _string_sanitize(string: str) -> str:
    """ Sanitize string method """
    banned_symbols = [
        '\r', '\n', '\t', '\\', '/', ' ', '<', '>', ';', ':', "'", '"',
        '[', ']', '|', '{', '}', '(', ')', '*', '&', '^', '%', '$', '#',
        '@', '!', '`', '~', ',', '.'
    ]

    for symbol in banned_symbols:
        string = string.replace(symbol, '')

    return string


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
        self.browsers_dict = self._get_default_browsers_dict()
        self._set_browsers_versions()
        self._set_default_browsers_version()
        self._set_browsers_base_name()
        ic(self.browsers_dict)

        # ic(self.config)

    def __call__(self):
        self.config_validation()

    def generate_result(self):
        pass

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

    def _get_default_browsers_dict(self):

        length = len(self.list_of_active_browsers)
        browsers_dict = dict(
            zip(
                self.list_of_active_browsers,
                [
                    {
                        'default-version': None,
                        'versions': [],
                        'base-name': None
                    } for _ in range(length)
                ]
            )
        )
        ic(browsers_dict)
        return browsers_dict

    def _set_browsers_versions(self) -> None:

        for i in range(self.count_of_all_browsers):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']

            if browser_object['use']:
                vnc, vnc_browser_name, vnc_versions, _ = _get_vnc_params(browser_object, browser_name)

                versions = self.browsers[i]['versions']

                if 'range' in versions:
                    _range_handler(browser_name, versions, self.browsers_dict[browser_name]['versions'])

                elif 'array' in versions:
                    _array_handler(browser_name, versions, self.browsers_dict[browser_name]['versions'])

                elif 'latest' in versions:
                    _latest_handler(browser_name, self.browsers_dict[browser_name]['versions'])

                if vnc:
                    if 'range' in vnc_versions:
                        _range_handler(vnc_browser_name, vnc_versions, self.browsers_dict[vnc_browser_name]['versions'])

                    elif 'array' in vnc_versions:
                        _array_handler(browser_name, vnc_versions, self.browsers_dict[vnc_browser_name]['versions'])

                    elif 'latest' in vnc_versions:
                        _latest_handler(vnc_browser_name, self.browsers_dict[vnc_browser_name]['versions'])

                    elif 'highest' in vnc_versions:
                        _highest_handler(
                            self.browsers_dict[browser_name]['versions'],
                            self.browsers_dict[vnc_browser_name]['versions']
                        )

                    _validation_boundary_conditions(
                        browser_name,
                        self.browsers_dict[vnc_browser_name]['versions'],
                        self.browsers_dict[browser_name]['versions']
                    )

                    _remove_same_values_from_array(
                        self.browsers_dict[vnc_browser_name]['versions'],
                        self.browsers_dict[browser_name]['versions']
                    )

                    if len(self.browsers_dict[browser_name]['versions']) < 1:
                        self.browsers_dict.pop(browser_name)

    def _set_default_browsers_version(self) -> None:

        for i in range(len(self.browsers)):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            vnc, vnc_browser_name, vnc_versions, vnc_default_version_object = _get_vnc_params(
                browser_object, browser_name
            )
            default_version_object = browser_object['default-version']

            if browser_name in self.browsers_dict:
                vnc_only = None
            else:
                vnc_only = True

            if not vnc_only:
                versions_list = self.browsers_dict[browser_name]['versions']
                # ic(versions_list)

                if 'custom' in default_version_object:
                    value = default_version_object['custom']
                elif 'highest' in default_version_object:
                    value = max(versions_list)
                elif 'minimal' in default_version_object:
                    value = min(versions_list)

                self.browsers_dict[browser_name]['default-version'] = value

            if vnc:
                vnc_versions_list = self.browsers_dict[vnc_browser_name]['versions']
                # ic(vnc_versions_list)

                if 'custom' in vnc_default_version_object:
                    value = vnc_default_version_object['custom']
                elif 'highest' in vnc_default_version_object:
                    value = max(vnc_versions_list)
                elif 'minimal' in vnc_default_version_object:
                    value = min(vnc_versions_list)

                self.browsers_dict[vnc_browser_name]['default-version'] = value

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

        for i in range(len(self.list_of_active_browsers)):
            if self.list_of_active_browsers[i] in available_browsers_in_registry:
                pass
            else:
                raise Exception(
                    f'Image "{self.list_of_active_browsers[i]}" not found '
                    f'in aerokube docker registry https://hub.docker.com/u/selenoid'
                )

    def _browser_version_existence_in_registry_check(self):

        available_browsers_versions_in_registry = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(len(self.list_of_active_browsers))])
        )

        for browser in self.browsers_dict:
            page_size_default = 25
            response_body = _docker_hub_get_request(
                'hub.docker.com',
                f'/v2/repositories/selenoid/{browser}/tags/',
                {'page_size': page_size_default}
            )

            for i in range(response_body['count']):
                available_browsers_versions_in_registry[browser].append(response_body['results'][i]['name'])

            # ic(available_browsers_versions_in_registry[browser])

            temp_versions_list = self.browsers_dict[browser]['versions']
            # ic(temp_versions_list)

            for i in range(len(temp_versions_list)):
                if str(temp_versions_list[i]) in available_browsers_versions_in_registry[browser]:
                    # ic(browser, temp_versions_list[i], "OK")
                    pass
                else:
                    raise Exception(
                        f'{browser}:{temp_versions_list[i]} not found into selenoid docker registry. '
                        f'Available versions: {available_browsers_versions_in_registry[browser]}'
                    )
        # ic(available_browsers_versions_in_registry)

    def _set_browsers_base_name(self) -> None:

        for i in range(len(self.browsers)):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            vnc, vnc_browser_name, vnc_versions, vnc_default_version_object = _get_vnc_params(
                browser_object, browser_name
            )
            browser_base_name = browser_object['base-name']
            ic(browser_base_name)

            if browser_name in self.browsers_dict:
                vnc_only = None
            else:
                vnc_only = True

            if not vnc_only:
                value = _string_sanitize(browser_base_name)

                self.browsers_dict[browser_name]['base-name'] = value

            if vnc:
                value = 'VNC_' + _string_sanitize(browser_base_name)
                self.browsers_dict[vnc_browser_name]['base-name'] = value
