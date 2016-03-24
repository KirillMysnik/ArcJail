from configparser import ConfigParser

from .paths import ARCJAIL_DATA_PATH


CONFIG_FILE = ARCJAIL_DATA_PATH / "config.ini"

config = ConfigParser()
config.read(CONFIG_FILE)
