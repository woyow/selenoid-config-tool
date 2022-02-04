import os
import sys

from icecream import ic


class ChangeRootDir:
    """ Change directory to be able to run main script in different directories """

    ic.disable()  # Disable logs into class

    def __init__(self) -> None:
        self.script_call_path = sys.argv[0]
        self.absolute_path = os.path.abspath(self.script_call_path)
        self.separator = os.sep
        self.script_file_name = self.absolute_path.split(self.separator)[-1]
        self.script_file_name_length = len(self.script_file_name)

        ic(self.script_call_path)
        ic(self.absolute_path)
        ic(self.script_file_name)

    def __call__(self) -> None:
        self.full_path = self._get_full_root_path()
        if self.full_path:
            self._change_dir()

    def _get_full_root_path(self) -> str:
        full_path = self.absolute_path[:-self.script_file_name_length]
        ic(full_path)
        return full_path

    def _change_dir(self) -> None:
        os.chdir(self.full_path)
        ic("Root dir has been changed")
