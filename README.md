# selenoid-config-tool
[![Linux only](https://www.kernel.org/theme/images/logos/favicon.png)]() **Only Linux support ;)**

Tool for [selenoid](https://github.com/aerokube/selenoid) and [ggr](https://github.com/aerokube/ggr) configs management. 
Automatically generating directories and `browsers.json`, `docker-compose.yaml`, `users.htpasswd` and `quota` files for selenoid and ggr.

# Features:
- [x] ggr
  - [x] config (browsers.json)
  - [x] quota (user.xml)
  - [x] docker-compose.yaml
  - [x] users.htpasswd
- [x] selenoid
  - [x] config (browsers.json)
  - [x] docker-compose.yaml
- [x] teams-quota / users-quota
  - [x] htpasswd
- [ ] hosts config
  - [x] standart parameters for selenoid (image, port, path)
  - [ ] optional parameters for selenoid (env, tmpfs, volumes, hosts, labels, sysctl, shmSize, cpu, mem)
  - [ ] shell-script for pull browsers images from browsers-config
- [ ] Dockerfile (for usage tool into docker)
- [ ] ??? Automatic deployment to tests servers via ssh
  - [ ] ??? Ansible playbooks

# Usage
## Download tool
1. Clone repository
```bash
cd ~
git clone git@github.com:woyow/selenoid-config-tool.git
```
2. Go to folder with tool
```bash
cd ~/selenoid-config-tool
```

## Fill config file

### 1. Create config.yaml file
```bash
cd ~/selenoid-config-tool/config
touch ./config.yaml
```

### 2. Fill browsers array
```yaml
browsers:
  - type: {{ image_name }}
    use: {{ bool }}
    vnc-image: # [optional]
      enable: {{ bool }}
      versions:
        # You can specify an array of the browsers you need using the `array` key
        array: {{ [array] }} # [float] array
        # OR
        # You can specify the range of versions you need in increments of 1 using the `range` key
        range:
          min: {{ min_value }} # float
          max: {{ max_value }} # float or latest
          ignore: {{ [array] }} # [optional] - [float] array
        # OR
        # You can specify the highest version from the docker registry using the `highest` key
        highest: true
    default-version:
      # You can specify the highest version from your version array using the `highest` key
      highest: true
      # OR
      # You can specify a custom version from your version array using the `custom` key.
      custom: {{ custom_value }} # float
      # OR
      # You can specify the minimal version from your version array using the `minimal` key
      minimal: true
    versions:
      # You can specify an array of the browsers you need using the `array` key
      array: {{ [array] }} # [float] array
      # OR
      # You can specify the range of versions you need in increments of 1 using the `range` key
      range:
        min: {{ min_value }} # float
        max: {{ max_value }} # float or latest
        ignore: {{ [array] }} # [optional] - [float] array
      # OR
      # You can specify the latest version from the docker registry using the `latest` key
      latest: true
```

### 3. Fill aerokube dictionary (selenoid + ggr declaration)
```yaml
aerokube:
  selenoid:
    image-version: {{ image_version }} # float or latest
    host-port: {{ port_value }}

  selenoid-ui: # [optional]
    image-version: {{ image_version }} # float or latest
    host-port: {{ port_value }}

  ggr: # [optional]
    image-version: {{ image_version }} # float or latest
    host-port: {{ port_value }}
    
  ggr-ui: # [optional]
    image-version: {{ image_version }} # float or latest
    host-port: {{ port_value }}
```

### 4. Fill hosts dictionary
```yaml
hosts:
  ggr:
    ip: {{ ip_value }}
    # OR/AND
    domain: {{ domain_value }}

  selenoid:
    # Array with regions
    - region:
        name: {{ region_name_value }}
        hosts: # array with hosts dictionaries
          - ip: {{ ip_value }}
            domain: {{ domain_value }} # [optional] - domain takes precedence over ip
            count: {{ count_value }} # [optional] - [default - 1]
            cpu-limit: {{ cpu_limit_value }} # [optional] - [default - 1]
            teams-quota: {{ [array] }} # [array] with team/user-name for quota
```

### 5. Fill teams quota array
```yaml
teams-quota: # [optional] - if use ggr balancer
  - name: {{ team_name_value }}
    password: {{ password_value }}
```

## Run script
### 1. Go to the folder and give execute permissions
```bash
cd ~/selenoid-config-tool
chmod u+x ./sctool
```
### 2. Install requirements
```bash
python3 -m pip install -r requirements.txt
```
### 3. Default usage
```bash
./sctool
```
### 4. Usage with parameters
#### 4.1 Get help
```bash
./sctool --help
```
#### 4.2 Run with custom parameters
```bash
./sctool --results-dir ./your-results-dir --config-dir ./your-config-dir
# or
./sctool -r ./your-results-dir -c ./your-config-dir
```

## Results
### 1. Change to the directory with the results
```bash
cd ~/selenoid-config-tool/results
```
### 2. Ready!

## Possible problems
The tool uses caching for http-responses. Therefore, in rare cases, you may not receive up-to-date information on browser versions. The cache is stored in the default folder for your user - `~/.cache/`
#### For remove cache, usage:
```bash
rm ~/.cache/selenoid_config_tool_requests_cache.sqlite
```