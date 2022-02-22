from helpers.config_parser import ConfigParser
from helpers.http_requests import HttpRequests
from helpers.file_generators import JsonGenerator
from helpers.file_generators import YamlGenerator
from helpers.file_system import FileSystem
from helpers.htpasswd import Htpasswd

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
) -> dict:
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


def _range_handler(browser_name: str, versions: dict, target_array: list) -> None:
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


def _array_handler(browser_name: str, versions: dict, target_array: list) -> None:
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


def _validation_boundary_conditions(browser_name: str, source_array: list, target_array: list) -> None:
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


def _get_vnc_params(browser: dict) -> (bool, dict) or (None, None):
    """
    Return the values you need to work with VNC browsers from config

    browser - browser object
    """

    key = 'vnc-image'
    enable_key = 'enable'
    versions_key = 'versions'

    if key in browser and browser[key][enable_key]:
        vnc = True
        vnc_versions = browser[key][versions_key]
    else:
        vnc = None
        vnc_versions = None

    return vnc, vnc_versions


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


def _is_image_type_valid(image_type: str, images: str or list) -> None:
    """ Return exception if image type not valid """
    if image_type in images:
        return
    else:
        raise Exception(f'image_type {image_type} not supported')


def _remove_old_dirs(root_path: str, actual_dirs: list) -> None:
    """ Remove dir from old configs """
    current_dirs = FileSystem(dir_name=root_path).get_dir_listing()
    actual_dirs = list(map(lambda x: x.split('/')[-1], actual_dirs))

    for directory in actual_dirs:
        try:
            current_dirs.remove(directory)
        except ValueError:
            continue

    for directory in current_dirs:
        path = root_path + '/' + directory
        ic(path)
        FileSystem(dir_name=path).remove_dir()


def _create_dirs(dir_array: list or str) -> None:
    """ Create dirs from list or string """
    if type(dir_array) is str:
        dir_array = [dir_array]

    if dir_array:
        for directory in dir_array:
            FileSystem(
                dir_name=directory
            ).create_dir()


def _remove_dirs(dir_array: list or str) -> None:
    """ Remove dirs from list or string """
    if type(dir_array) is str:
        dir_array = [dir_array]

    if dir_array:
        for directory in dir_array:
            FileSystem(
                dir_name=directory
            ).remove_dir()


class Configurator:

    # ic.disable()
    ic.enable()

    def __init__(self) -> None:

        # Parsing yaml config
        self.config_parser = ConfigParser()
        self.browsers, self.aerokube, self.hosts, self.teams = self.config_parser()

        # Pre-validation
        self._browser_count_check()

        # Variables for browsers from config
        self.count_of_all_browsers = self._get_count_of_all_browsers()
        self.list_of_active_browsers = self._get_active_browsers_list()
        self.browsers_dict = self._get_default_browsers_dict()
        self._set_browsers_versions()
        self._set_default_browsers_version()
        ic(self.browsers_dict)

        # Browser validations
        self._check_browser_existence_in_docker_registry()
        self._check_browser_version_existence_in_docker_registry()

        # Variables for aerokube from config
        self.aerokube_dict = self._get_default_aerokube_dict()
        self._set_aerokube_images_version()
        self._set_aerokube_host_ports()
        ic(self.aerokube_dict)

        # Variables for hosts from config
        self.hosts_dict = self._get_default_hosts_dict()
        self._hosts_setter()
        ic(self.hosts_dict)

        # Variables for teams from config
        self.teams_dict = self._get_default_teams_dict()
        self._teams_setter()
        ic(self.teams_dict)

    def __call__(self) -> None:
        self.configurate()

    def configurate(self) -> None:
        """ Create config dirs and files """
        ggr_root_path = './results/ggr'
        selenoid_root_path = './results/selenoid'

        config_path = '/config'
        quota_path = '/quota'

        ggr_hosts_paths = []
        selenoid_hosts_paths = []

        paths_for_create = []
        paths_for_remove = []

        ggr_key = 'ggr'
        selenoid_key = 'selenoid'
        ip_key = 'ip'
        domain_key = 'domain'

        if ggr_key in self.hosts_dict:
            count = len(self.hosts_dict[ggr_key])

            for i in range(count):
                ggr_object = self.hosts_dict[ggr_key][i]

                if ggr_object[domain_key] or (ggr_object[ip_key] and ggr_object[domain_key]):
                    ggr_hosts_paths.append(ggr_root_path + '/' + ggr_object[domain_key])
                elif ggr_object[ip_key]:
                    ggr_hosts_paths.append(ggr_root_path + '/' + ggr_object[ip_key])

                paths_for_create.append(ggr_hosts_paths[i] + config_path)
                paths_for_create.append(ggr_hosts_paths[i] + quota_path)
        else:
            paths_for_remove.append(ggr_root_path)

        if 'selenoid' in self.hosts_dict:
            count = len(self.hosts_dict[selenoid_key])

            for i in range(count):
                selenoid_object = self.hosts_dict[selenoid_key][i]

                if selenoid_object[domain_key] or (selenoid_object[ip_key] and selenoid_object[domain_key]):
                    selenoid_hosts_paths.append(selenoid_root_path + '/' + selenoid_object[domain_key])
                elif selenoid_object[ip_key]:
                    selenoid_hosts_paths.append(selenoid_root_path + '/' + selenoid_object[ip_key])

                paths_for_create.append(selenoid_hosts_paths[i] + config_path)
        else:
            paths_for_remove.append(selenoid_root_path)

        _remove_old_dirs(ggr_root_path, ggr_hosts_paths)
        _remove_old_dirs(selenoid_root_path, selenoid_hosts_paths)
        _create_dirs(paths_for_create)
        _remove_dirs(paths_for_remove)

        self._create_browsers_json(ggr_hosts_paths, selenoid_hosts_paths, config_path)
        self._create_docker_compose_yaml(ggr_hosts_paths, selenoid_hosts_paths)
        self._create_htpasswd_file(ggr_hosts_paths)

    def _create_browsers_json(self, ggr_hosts_paths: list, selenoid_hosts_paths: list, config_path: str) -> None:
        """ Create browsers.json file into ggr and selenoid dirs """

        file_name = 'browsers.json'
        browsers_json_dict = self._generate_selenoid_browsers_json_file()
        paths_for_config = ggr_hosts_paths + selenoid_hosts_paths

        for path in paths_for_config:
            path += config_path
            JsonGenerator(
                browsers_json_dict,
                path + '/' + file_name
            ).json_data_dump_to_file()

    def _create_docker_compose_yaml(self, ggr_hosts_paths: list, selenoid_hosts_paths: list) -> None:
        """ Create docker-compose.yaml file into ggr and selenoid dirs """

        file_name = 'docker-compose.yaml'
        selenoid_image_type = 'selenoid'
        ggr_image_type = 'ggr'

        ggr_docker_compose_yaml_dict = self._generate_docker_compose_yaml_file(ggr_image_type)
        selenoid_docker_compose_yaml_dict = self._generate_docker_compose_yaml_file(selenoid_image_type)

        if ggr_hosts_paths:
            for path in ggr_hosts_paths:
                host = path.split('/')[-1]
                docker_compose_dict = ggr_docker_compose_yaml_dict[host]
                YamlGenerator(
                    docker_compose_dict,
                    path + '/' + file_name
                ).yaml_data_dump_to_file()

        if selenoid_hosts_paths:
            for path in selenoid_hosts_paths:
                host = path.split('/')[-1]
                docker_compose_dict = selenoid_docker_compose_yaml_dict[host]
                YamlGenerator(
                    docker_compose_dict,
                    path + '/' + file_name
                ).yaml_data_dump_to_file()

    def _create_htpasswd_file(self, ggr_hosts_paths):
        file_name = 'users.htpasswd'
        name_key = 'name'
        pass_key = 'password'
        teams_key = 'teams-quota'

        if ggr_hosts_paths:
            for path in ggr_hosts_paths:
                teams_object = self.teams_dict[teams_key]

                count = len(teams_object)
                for i in range(count):
                    Htpasswd(
                        dir_name=path,
                        file_name=file_name,
                        name=teams_object[i][name_key],
                        password=teams_object[i][pass_key]
                    ).add_user()

    def _browser_count_check(self) -> None:
        """ Validation: count of browsers > 0 """
        count = len(self.browsers)
        if count < 1:
            raise Exception('You must use at least one browser in your config')

    def _get_count_of_all_browsers(self) -> int:
        """ Return count of browsers in config """
        return len(self.browsers)

    def _get_active_browsers_list(self) -> list:
        """ Get list browsers with key and value 'use': true in config """
        browsers = []

        for i in range(self.count_of_all_browsers):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            if self.browsers[i]['use'] is True:
                browsers.append(browser_name)

        return browsers

    def _get_default_browsers_dict(self) -> dict:
        """ Get default dictionary template for browsers """

        length = len(self.list_of_active_browsers)
        browsers_dict = dict(
            zip(
                self.list_of_active_browsers,
                [
                    {
                        'default-version': None,
                        'versions': [],
                        'vnc-versions': []
                    } for _ in range(length)
                ]
            )
        )

        return browsers_dict

    def _set_browsers_versions(self) -> None:
        """ Set 'versions' values into browser's dictionary """

        for i in range(self.count_of_all_browsers):
            browser_object = self.browsers[i]
            browser_name = browser_object['type']
            use_key = 'use'

            if browser_object[use_key]:
                versions_key = 'versions'
                range_key = 'range'
                array_key = 'array'
                latest_key = 'latest'
                versions = self.browsers[i][versions_key]

                if range_key in versions:
                    _range_handler(browser_name, versions, self.browsers_dict[browser_name][versions_key])

                elif array_key in versions:
                    _array_handler(browser_name, versions, self.browsers_dict[browser_name][versions_key])

                elif latest_key in versions:
                    _latest_handler(browser_name, self.browsers_dict[browser_name][versions_key])

                vnc, vnc_versions = _get_vnc_params(browser_object)
                if vnc:
                    vnc_versions_key = 'vnc-versions'
                    highest_key = 'highest'
                    if range_key in vnc_versions:
                        _range_handler(browser_name, vnc_versions, self.browsers_dict[browser_name][vnc_versions_key])

                    elif array_key in vnc_versions:
                        _array_handler(browser_name, vnc_versions, self.browsers_dict[browser_name][vnc_versions_key])

                    elif latest_key in vnc_versions:
                        _latest_handler(browser_name, self.browsers_dict[browser_name][vnc_versions_key])

                    elif highest_key in vnc_versions:
                        _highest_handler(
                            self.browsers_dict[browser_name][versions_key],
                            self.browsers_dict[browser_name][vnc_versions_key]
                        )

                    _validation_boundary_conditions(
                        browser_name,
                        self.browsers_dict[browser_name][vnc_versions_key],
                        self.browsers_dict[browser_name][versions_key]
                    )

                    _remove_same_values_from_array(
                        self.browsers_dict[browser_name][vnc_versions_key],
                        self.browsers_dict[browser_name][versions_key]
                    )

                    # if len(self.browsers_dict[browser_name][versions_key]) < 1:
                    #    self.browsers_dict.pop(browser_name)

    def _set_default_browsers_version(self) -> None:
        """ Set 'default-version' values into browser's dictionary """
        type_key = 'type'
        default_version_key = 'default-version'
        versions_key = 'versions'
        vnc_versions_key = 'vnc-versions'
        custom_key = 'custom'
        highest_key = 'highest'
        minimal_key = 'minimal'

        for i in range(len(self.browsers)):
            browser_object = self.browsers[i]
            browser_name = browser_object[type_key]
            default_version_object = browser_object[default_version_key]

            versions_list = (
                    self.browsers_dict[browser_name][versions_key] + self.browsers_dict[browser_name][vnc_versions_key]
            )

            # ic(versions_list)

            if custom_key in default_version_object:
                value = default_version_object[custom_key]
            elif highest_key in default_version_object:
                value = max(versions_list)
            elif minimal_key in default_version_object:
                value = min(versions_list)

            self.browsers_dict[browser_name][default_version_key] = value

    def _check_browser_existence_in_docker_registry(self) -> None:
        """ Validation: All browsers must exist in the docker registry """

        page_size_default = 25
        response_body = _docker_hub_get_request(
            'hub.docker.com',
            '/v2/repositories/selenoid',
            {'page_size': page_size_default}
        )

        images_count = response_body['count']
        available_browsers_in_registry = []

        for i in range(images_count):
            browser_name = response_body['results'][i]['name']
            available_browsers_in_registry.append(browser_name)

        for i in range(len(self.list_of_active_browsers)):
            if self.list_of_active_browsers[i] in available_browsers_in_registry:
                pass
            else:
                raise Exception(
                    f'Image "{self.list_of_active_browsers[i]}" not found '
                    f'in aerokube docker registry https://hub.docker.com/u/selenoid'
                )

    def _check_browser_version_existence_in_docker_registry(self) -> None:
        """ Validation: All browser versions must exist in the docker registry """

        length = len(self.list_of_active_browsers)
        available_browsers_versions_in_registry = dict(
            zip(self.list_of_active_browsers, [[] for _ in range(length)])
        )

        for browser in self.browsers_dict:
            page_size_default = 25
            response_body = _docker_hub_get_request(
                'hub.docker.com',
                f'/v2/repositories/selenoid/{browser}/tags/',
                {'page_size': page_size_default}
            )

            count = response_body['count']
            for i in range(count):
                value = response_body['results'][i]['name']
                available_browsers_versions_in_registry[browser].append(value)

            temp_versions_list = self.browsers_dict[browser]['versions']
            length = len(temp_versions_list)
            for i in range(length):
                version = str(temp_versions_list[i])
                if version in available_browsers_versions_in_registry[browser]:
                    pass
                else:
                    raise Exception(
                        f'{browser}:{version} not found into selenoid docker registry. '
                        f'Available versions: {available_browsers_versions_in_registry[browser]}'
                    )
        # ic(available_browsers_versions_in_registry)

    def _get_default_aerokube_dict(self) -> dict:
        """ Get default dictionary template for aerokube """

        aerokube_dict = {
            'selenoid': {
                'image-version': None,
                'host-port': None
            }
        }

        if 'selenoid-ui' in self.aerokube:
            aerokube_dict.update(
                {
                    'selenoid-ui': {
                        'image-version': None,
                        'host-port': None
                    }
                }
            )

        if 'ggr' in self.aerokube:
            aerokube_dict.update(
                {
                    'ggr': {
                        'image-version': None,
                        'host-port': None,
                        'encrypt-connection': None
                    }
                }
            )

        if 'ggr-ui' in self.aerokube:
            aerokube_dict.update(
                {
                    'ggr-ui': {
                        'image-version': None,
                        'host-port': None
                    }
                }
            )

        return aerokube_dict

    def _set_aerokube_images_version(self) -> None:
        """ Set 'image-version' values into aerokube's dictionary """

        for image_name in self.aerokube_dict:
            value = self.aerokube[image_name]['image-version']
            self.aerokube_dict[image_name]['image-version'] = value

    def _set_aerokube_host_ports(self) -> None:
        """ Set 'host-port' values into aerokube's dictionary """

        for image_name in self.aerokube_dict:
            value = self.aerokube[image_name]['host-port']
            if not 0 < value < 65535:
                raise Exception(f'port value for aerokube/{image_name} must be 0...65535')
            self.aerokube_dict[image_name]['host-port'] = value

    def _get_default_hosts_dict(self) -> dict:
        """ Get default dictionary template for hosts """

        hosts_dict = {
            'selenoid': [
                {
                    'ip': None,
                    'domain': None,
                    'count': None,
                    'cpu-limit': None,
                    'teams-quota': None,
                    'region-name': None,
                    'vnc': {
                        'ip': None,
                        'port': None
                    }
                } for _ in range(len(self.hosts['selenoid']))
            ]
        }

        if 'ggr' in self.hosts:
            hosts_dict.update(
                {
                    'ggr': [
                        {
                            'ip': None,
                            'domain': None
                        } for _ in range(len(self.hosts['ggr']))
                    ],
                }
            )

        return hosts_dict

    def _hosts_setter(self):

        if 'ggr' in self.hosts:
            image_type = 'ggr'
            ggr_length = len(self.hosts[image_type])

            for count in range(ggr_length):
                hosts_object = self.hosts[image_type][count]
                args = (hosts_object, image_type, count)
                self._set_hosts_ip(*args)
                self._set_hosts_domain(*args)

        selenoid_length = len(self.hosts['selenoid'])
        image_type = 'selenoid'

        for count in range(selenoid_length):
            hosts_object = self.hosts[image_type][count]
            args = (hosts_object, image_type, count)
            self._set_hosts_ip(*args)
            # self._set_hosts_port(*args)  # port set in aerokube/selenoid/host-port
            self._set_hosts_domain(*args)
            self._set_hosts_count(*args)
            self._set_hosts_cpu_limit(*args)
            self._set_hosts_teams_quota(*args)
            self._set_hosts_region_name(*args)
            self._set_hosts_vnc(*args)

    def _set_hosts_ip(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'ip' values into hosts dictionary """

        key = 'ip'
        images = ('ggr', 'selenoid')

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]
        else:
            return

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_port(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'port' values into hosts dictionary """

        key = 'port'
        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]
            if not 0 < value < 65535:
                raise Exception(f'port value for {image_type}[{counter}] must be 0...65535')

        else:
            value = 4444  # Default port for selenoid api

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_domain(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'domain' values into hosts dictionary """

        key = 'domain'
        images = ('ggr', 'selenoid')

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]
        else:
            return

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_count(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'count' values into hosts dictionary """

        key = 'count'
        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]

            if not isinstance(value, int):
                raise Exception(f'count priority for {image_type}[{counter}] must be of type integer')

            if value < 1:
                raise Exception(f'count priority for for {image_type}[{counter}] can not be less then 1')
        else:
            value = 1  # Default value for load balancing priority

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_cpu_limit(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'cpu-limit' values into hosts dictionary """

        key = 'cpu-limit'
        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]

            if not isinstance(value, int):
                raise Exception(f'cpu-limit for {image_type}[{counter}] must be of type integer')

            if value < 1:
                raise Exception(f'cpu-limit for {image_type}[{counter}] can not be less then 1')
        else:
            value = 1  # Default value for cpu-limit

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_teams_quota(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'teams-quota' values into hosts dictionary """

        key = 'teams-quota'
        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]
            value = list(map(_string_sanitize, value))
        else:
            return

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_region_name(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'region-name' values into hosts dictionary """

        key = 'region-name'
        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            value = hosts_object[key]
            value = _string_sanitize(value)
        else:
            return

        self.hosts_dict[image_type][counter][key] = value

    def _set_hosts_vnc(self, hosts_object: dict, image_type: str, counter: int) -> None:
        """ Set 'vnc' values into hosts dictionary """

        key = 'vnc'
        ip_key = 'ip'
        port_key = 'port'

        images = 'selenoid'

        _is_image_type_valid(image_type, images)

        if key in hosts_object:
            vnc_object = hosts_object[key]
            value_ip = vnc_object[ip_key]
            value_port = vnc_object[port_key]
        else:
            return

        self.hosts_dict[image_type][counter][key][ip_key] = value_ip
        self.hosts_dict[image_type][counter][key][port_key] = value_port

    def _get_default_teams_dict(self) -> dict:
        """ Get default dictionary template for teams """

        teams_dict = {
            'teams-quota': [
                {
                    'name': None,
                    'password': None
                } for _ in range(len(self.teams))
            ]
        }

        return teams_dict

    def _teams_setter(self):
        """ Set teams values from config """
        teams_count = len(self.teams)
        if teams_count > 0:
            for count in range(teams_count):
                self._set_teams_names(count)
                self._set_teams_passwords(count)

    def _set_teams_names(self, count: int) -> None:
        key = 'name'
        teams_quota_key = 'teams-quota'
        value = self.teams[count][key]
        self.teams_dict[teams_quota_key][count][key] = value

    def _set_teams_passwords(self, count: int) -> None:
        key = 'password'
        teams_quota_key = 'teams-quota'
        value = self.teams[count][key]
        self.teams_dict[teams_quota_key][count][key] = value

    def _get_default_browsers_json_dict(self) -> dict:

        browsers_dict = {
            browser: {
                'default': None,
                'versions': {}
            } for browser in self.browsers_dict
        }

        return browsers_dict

    def _generate_selenoid_browsers_json_file(self) -> dict:
        browsers_dict = self._get_default_browsers_json_dict()
        versions = ('versions', 'vnc-versions')

        for browser in self.browsers_dict:
            browsers_dict[browser]['default'] = str(self.browsers_dict[browser]['default-version'])

            for version_key in versions:
                for version in self.browsers_dict[browser][version_key]:
                    version = str(version)

                    browsers_dict[browser]['versions'][version] = {}

                    # Variables
                    if version_key == 'vnc-versions':
                        image = f'selenoid/vnc_{browser}:{version}'
                    else:
                        image = f'selenoid/{browser}:{version}'

                    port = f"{self.aerokube['selenoid']['host-port']}"
                    path = '/'
                    env = None
                    tmpfs = None
                    volumes = None
                    hosts = None
                    labels = None
                    sysctl = None
                    shm_size = None
                    cpu = None
                    mem = '128m'

                    if image:
                        browsers_dict[browser]['versions'][version]['image'] = image

                    if port:
                        browsers_dict[browser]['versions'][version]['port'] = port

                    if path:
                        browsers_dict[browser]['versions'][version]['path'] = path

                    if env:
                        browsers_dict[browser]['versions'][version]['env'] = env

                    if tmpfs:
                        browsers_dict[browser]['versions'][version]['tmpfs'] = tmpfs

                    if volumes:
                        browsers_dict[browser]['versions'][version]['volumes'] = volumes

                    if hosts:
                        browsers_dict[browser]['versions'][version]['hosts'] = hosts

                    if labels:
                        browsers_dict[browser]['versions'][version]['labels'] = labels

                    if sysctl:
                        browsers_dict[browser]['versions'][version]['sysctl'] = sysctl

                    if shm_size:
                        browsers_dict[browser]['versions'][version]['shmSize'] = shm_size

                    if cpu:
                        browsers_dict[browser]['versions'][version]['cpu'] = cpu

                    if mem:
                        browsers_dict[browser]['versions'][version]['mem'] = mem

        return browsers_dict

    def _get_default_docker_compose_yaml_dict(self, image_type: str) -> dict:
        """ Get default template for docker-compose.yaml dict """

        ip_key = 'ip'
        domain_key = 'domain'
        docker_compose_dict = {}

        if image_type in self.hosts_dict:
            count = len(self.hosts_dict[image_type])
            for i in range(count):
                image_object = self.hosts_dict[image_type][i]

                if image_object[domain_key] or (image_object[ip_key] and image_object[domain_key]):
                    key = domain_key
                elif image_object[ip_key]:
                    key = ip_key

                docker_compose_dict.update(
                    {
                        image_object[key]: {
                            'version': '3',
                            'services': {}
                        }
                    }
                )

        return docker_compose_dict

    def _generate_docker_compose_yaml_file(self, image_type: str) -> dict:
        """ Generate docker-compose.yaml dict """

        docker_compose_dict = self._get_default_docker_compose_yaml_dict(image_type)
        services_key = 'services'
        selenoid_key = 'selenoid'
        selenoid_ui_key = 'selenoid-ui'
        ggr_key = 'ggr'
        ggr_ui_key = 'ggr-ui'
        host_port_key = 'host-port'
        image_version_key = 'image-version'
        cpu_limit_key = 'cpu-limit'

        counter = 0
        for host in docker_compose_dict:
            if image_type == 'selenoid':
                if selenoid_key in self.aerokube:
                    selenoid_dict = {
                        'selenoid': {
                            'image': f"aerokube/selenoid:{self.aerokube_dict[selenoid_key][image_version_key]}",
                            'network_mode': 'bridge',
                            'ports': [
                                f"{self.aerokube_dict[selenoid_key][host_port_key]}:"
                                f"{self.aerokube_dict[selenoid_key][host_port_key]}"
                            ],
                            'volumes': [
                                '/var/run/docker.sock:/var/run/docker.sock',
                                './config/:/etc/selenoid/:ro'
                            ],
                            'command': [
                                '-limit',
                                f"{self.hosts_dict[selenoid_key][counter][cpu_limit_key]}",
                                '-listen',
                                f":{self.aerokube_dict[selenoid_key][host_port_key]}"
                            ]
                        }
                    }

                    docker_compose_dict[host][services_key].update(selenoid_dict)

                if selenoid_ui_key in self.aerokube:
                    selenoid_ui_dict = {
                        'selenoid-ui': {
                            'image': f"aerokube/selenoid-ui:{self.aerokube_dict[selenoid_ui_key][image_version_key]}",
                            'network_mode': 'bridge',
                            'ports': [
                                f"{self.aerokube_dict[selenoid_ui_key][host_port_key]}:"
                                f"{self.aerokube_dict[selenoid_ui_key][host_port_key]}"
                            ],
                            'links': [
                                'selenoid'
                            ],
                            'command': [
                                '--selenoid-uri',
                                f"http://{selenoid_key}:{self.aerokube_dict[selenoid_key][host_port_key]}",
                                '-listen',
                                f":{self.aerokube_dict[selenoid_ui_key][host_port_key]}"
                            ]
                        }
                    }
                    docker_compose_dict[host][services_key].update(selenoid_ui_dict)

            elif image_type == 'ggr':
                if ggr_key in self.aerokube:
                    ggr_dict = {
                        'ggr': {
                            'restart': 'always',
                            'image': f"aerokube/ggr:{self.aerokube_dict[ggr_key][image_version_key]}",
                            'ports': [
                                f"{self.aerokube_dict[ggr_key][host_port_key]}:"
                                f"{self.aerokube_dict[ggr_key][host_port_key]}"
                            ],
                            'volumes': [
                                './:/etc/grid-router:ro'
                            ],
                            'command': [
                                '-quotaDir',
                                '/etc/grid-router/quota',
                                '-listen',
                                f":{self.aerokube_dict[ggr_key][host_port_key]}"
                            ]
                        }
                    }
                    docker_compose_dict[host][services_key].update(ggr_dict)

                if ggr_ui_key in self.aerokube:
                    ggr_ui_dict = {
                        'ggr-ui': {
                            'image': f"aerokube/ggr:{self.aerokube_dict[ggr_key][image_version_key]}",
                            'ports': [
                                f"{self.aerokube_dict[ggr_ui_key][host_port_key]}:"
                                f"{self.aerokube_dict[ggr_ui_key][host_port_key]}"
                            ],
                            'links': [
                                'ggr'
                            ],
                            'volumes': [
                                './:/etc/grid-router:ro'
                            ],
                            'command': [
                                '-quota-dir',
                                '/etc/grid-router/quota',
                                '-listen',
                                f":{self.aerokube_dict[ggr_ui_key][host_port_key]}"
                            ]
                        }
                    }
                    docker_compose_dict[host][services_key].update(ggr_ui_dict)

            counter += 1

        return docker_compose_dict
