import json


class Generator:

    def __init__(self, data: dict, file_path: str) -> None:
        self.data = data
        self.file_path = file_path

    def __call__(self) -> None:
        self.json_data_dump_to_file()

    def json_data_dump_to_file(self) -> None:
        with open(self.file_path, 'w') as json_file:
            json.dump(self.data, json_file, sort_keys=True, indent=4)
