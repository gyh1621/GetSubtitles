# coding: utf-8

import shutil
import pkg_resources
import configparser
from os import path, makedirs

from appdirs import *

appname = "getsub"
user_config_path = path.join(user_config_dir(appname), "getsub.conf")
default_config_path = pkg_resources.resource_filename(__name__, "default.conf")

# create user config if not exist
if not path.exists(user_config_path):
    if not path.exists(path.dirname(user_config_path)):
        makedirs(path.dirname(user_config_path))
    shutil.copyfile(default_config_path, user_config_path)

config = configparser.ConfigParser()

try:
    config.read(user_config_path)
except Exception as e:
    print("error reading", user_config_path, e)
assert config.sections()
