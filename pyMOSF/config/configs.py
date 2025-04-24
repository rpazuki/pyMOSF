"""Configuartion/setting module.

   Notes:
   ------
       1- Configurations are readonly, and are stored in 'resource' folder.
       2- Setting are writable and are stored in users' data folder,
          dependening on the os.
"""
from __future__ import annotations

import json
import platform
from enum import Enum
from pathlib import Path

from addict import Dict as DefaultDict


class GUIFramework(str, Enum):
    TOGA = "TOGA"
    KIVY = "KIVY"
    UKNOWN = "UKNOWN"


class Dict(DefaultDict):
    def __missing__(self, key) -> None:
        # raise KeyError(key)
        # calling dict.unassinged properties return None
        return None


class _Dict(DefaultDict):
    def __missing__(self, key):
        raise KeyError(key)


class Settings(DefaultDict):
    __instance = None
    __is_changed = False
    __loading_path = ""
    FILE_NAME = "settings.json"

    def __init__(__self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def load(data_path, default_conf={}) -> Settings:
        if Settings.__instance is None:
            try:

                with open(data_path / Settings.FILE_NAME, "r") as f:
                    __setting = json.load(f)
                    Settings.__loading_path = str(
                        data_path / Settings.FILE_NAME)

                    # Todo:Update thye default setting if new version
                    # has new entry.

                    Settings.__instance = Settings(**__setting)
                    # Check if the settings are empty
                    # and set the default settings

            except FileNotFoundError:
                Path(data_path).mkdir(parents=True, exist_ok=True)
                ###################################
                # Define the default settings here
                with open(data_path / Settings.FILE_NAME, "w") as f:
                    json.dump(default_conf, f, indent=4)
                    Settings.__loading_path = str(
                        data_path / Settings.FILE_NAME)
                Settings.__instance = Settings(**default_conf)
                Settings.__is_changed = False

        return Settings.__instance

    def __setitem__(self, name, value):
        Settings.__is_changed = True
        return super().__setitem__(name, value)

    def save(self):
        with open(Settings.__loading_path, "w") as f:
            json.dump(self, f, indent=4)
            Settings.__is_changed = False

    def on_end(self):
        if Settings.__is_changed:
            self.save()


class Configurable:
    def on_common_config(self):
        pass

    def on_linux_config(self):
        pass

    def on_darwin_config(self):
        pass

    def on_ios_config(self):
        pass

    def on_ipados_config(self):
        pass

    def on_windows_config(self):
        pass

    def on_others_config(self):
        raise NotImplementedError()

    def _set_config(self):
        """Layout related config (e.g. bindings).
        """
        self.on_common_config()
        os = platform.system().lower()
        match os:
            case "linux":
                self.on_linux_config()
            case "darwin":
                self.on_darwin_config()
            case "ios":
                self.on_ios_config()
            case "ipados":
                self.on_ipados_config()
            case "windows":
                self.on_windows_config()
            case _:
                self.on_others_config()
