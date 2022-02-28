#! /usr/bin/env python3

import argparse
import sys

from helpers.change_root_dir import ChangeRootDir
from helpers.config_parser import ConfigParser
from src.configurator import Configurator
from helpers.open_config_file import OpenFile


def init() -> None:
    try:
        change_root_dir = ChangeRootDir()
        change_root_dir()  # Change directory to be able to run script in different directories
    except:
        print("Something went wrong. Root directory not changed.")
    finally:
        del change_root_dir


def main() -> None:
    init()

    configurator = Configurator()
    configurator()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='main.py')
    parser.add_argument('-d', '--dir', default='/results', help='Directory to save results, default - ./results')

    cmd_args = parser.parse_args()
    print(cmd_args)
    sys.exit(main())
