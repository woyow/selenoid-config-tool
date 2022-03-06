import yaml


class Generator:

	def __init__(self, data: dict, file_path: str) -> None:
		self.data = data
		self.file_path = file_path

	def __call__(self) -> None:
		self.yaml_data_dump_to_file()

	def yaml_data_dump_to_file(self) -> None:
		with open(self.file_path, 'w') as yaml_file:
			yaml.dump(self.data, yaml_file, allow_unicode=True)
