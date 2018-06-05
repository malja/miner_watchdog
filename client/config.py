import configparser
from os.path import exists, isfile
from collections import namedtuple


class Config(object):
    """
    Class for loading INI configuration file into a namedtuple.
    """

    def __init__(self, logger):

        self._path = ""
        self._content = None
        self._parser = configparser.ConfigParser()
        self.logger = logger.getChild("config")

    def open(self, path):

        if not (exists(path) and isfile(path)):
            self.logger.error("Configuration file '{}' does not exist.".format(path))
            return False

        self.path = path

        if len(self._parser.read(path, "UTF8")) != 1:
            self.logger.error("Unable to read configuration file '{}'".format(path))
            return False

        data = {}

        for section in self._parser.sections():
            data[section] = {}

            for key in self._parser.options(section):
                data[section][key] = self._parser.get(section, key)

        self._content = self._convert_dict_to_namedtuple(data)

    def _convert_dict_to_namedtuple(self, d):
        """
        
        """
        for k, v in d.items():
            if isinstance(v, dict):
                d[k] = self._convert_dict_to_namedtuple(v)
        return namedtuple('object', d.keys())(*d.values())

    def __getattr__(self, item):
        if hasattr(self._content, item):
            return getattr(self._content, item)

        raise AttributeError()