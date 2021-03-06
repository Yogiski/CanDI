#data.py loads data automatically and contains methods for loading data via user input
import os
import gc
import operator
import json
import configparser
from pathlib import Path
import pandas as pd
import numpy as np
import sys



class Data(object):
#Class data is used for loading and caching data
#can be tuned to load specific datasets upon import by editing config.ini
#can call Data.load() to load any specific dataset
    def __init__(self):

        self._file_path = Path(os.path.dirname(os.path.realpath(__file__)))
        config_path = self._file_path / 'data/config.ini'

        parser = configparser.ConfigParser()
        parser.read(config_path)

        self._parser = parser
        self._verify_install()
        self._init_sources()
        self._init_depmap_paths()
        self._init_index_tables()

    def _verify_install(self):
        try:
            assert "depmap_urls" in self._parser.sections()
        except AssertionError:
            raise(RuntimeError, "CanDI has not been properly installed. Please run CanDI/install.py prior to import")

    def _init_sources(self):

        sources = []

        for option in self._parser["data_paths"]:
            sources.append(option)
            setattr(self, "_" + option + "_path", self._file_path / self._parser["data_paths"][option])

        self.sources = sources

    def _init_depmap_paths(self):
        self.depmap_files = self._parser["depmap_files"]

        for option in self._parser["depmap_files"]:
            try:
                new_path = self._depmap_path / self._parser.get("depmap_files", option)
                assert os.path.exists(new_path)
                setattr(self, option, new_path)
            except AssertionError:
                setattr(self, option, None)

    def _init_index_tables(self):

        for option in self._parser["autoload_info"]:
            try:
               new_path = self._file_path / self._parser.get("autoload_info", option)
               assert os.path.exists(new_path)
               setattr(self, option, self._handle_autoload(option, new_path))
            except AssertionError:
               raise(RuntimeError, "You are missing essential index table: {}. exiting...".format(new_path))


    @staticmethod
    def _handle_autoload(method, path):

        if method == "genes":

            df = pd.read_csv(path,
                             memory_map=True,
                             low_memory=False,
                             dtype={"ENTREZ ID":str},
                             index_col = "Approved symbol")

        elif method == "cell_lines":

            df = pd.read_csv(path,
                             memory_map=True,
                             low_memory=False,
                             index_col="DepMap_ID")

        elif method == "locations":
            df = pd.read_csv(path,
                             memory_map=True,
                             low_memory=True)

        return df


    def load(self, key):
        if hasattr(self, key):

            new_path = getattr(self, key)
            try:
                index = self._parser.get("index", key)

            except configparser.NoOptionError:
                index = None

            except AttributeError:
                raise RuntimeError("This package is not compatible with python2. Make sure you're using a Python3 interpreter")

            df = pd.read_csv(new_path,
                             memory_map = True,
                             low_memory = False,
                             index_col = index)

            setattr(self, key, df)
            return getattr(self, key)

        else:
            raise KeyError("{0} cannot find file {1}".format(self, key))

    def unload(self, key):

        setattr(self, key, self.data_path + self._parser["files"][key])
        gc.collect()
