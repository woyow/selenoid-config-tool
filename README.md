# selenoid-config-tool
Tool for management selenoid and ggr configs. 
Automatically generating directories and `browsers.json`, `docker-compose.yaml`, `users.htpasswd` and `quota` files for selenoid and ggr.

# Usage
## Download tool
1. Clone repository
```bash
[~] $ git clone git@github.com:woyow/selenoid-config-tool.git
```
2. Go to folder with tool
```bash
[~] $ cd ./selenoid-config-tool
```

## Fill config file

### 1. Create config.yaml file
```bash
[~/selenoid-config-tool] $ cd ./config
[~/selenoid-config-tool/config] $ touch ./config.yaml
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
      # You can specify the highest version from your version array using the `minimal` key
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

  ggr:
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

## Results
### 1. Change to the directory with the results
```bash
[~/selenoid-config-tool] $ cd ./results
```
### 2. Ready!