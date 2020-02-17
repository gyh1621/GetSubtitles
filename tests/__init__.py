import os
from os import path


def create_file(path):
    with open(path, "w"):
        pass


def create_test_directory(dir_structure, parent_dir="testtmp"):
    if not path.exists(parent_dir):
        os.mkdir(parent_dir)
    for k, v in dir_structure.items():
        if v is None:  # file
            create_file(path.join(parent_dir, k))
            continue
        os.mkdir(path.join(parent_dir, k))
        for f in v:
            create_file(path.join(parent_dir, k, f))
