"""Configuartion/setting module.

   Notes:
   ------
       1- Configurations are readonly, and are stored in 'resource' folder.
       2- Setting are writable and are stored in users' data folder,
          dependening on the os.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
from enum import Enum
from pathlib import Path

import pytoml as tomllib  # tomllib
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


class _Config(_Dict):

    @property
    def gui_framework(self) -> GUIFramework:
        if "framework" not in self or "framework.name" in self:
            return GUIFramework.UKNOWN

        return GUIFramework[self.framework.name.upper()]


config_file_path = os.path.join(os.path.dirname(__file__), 'config.toml')
with open(config_file_path, "rb") as f:
    __config = tomllib.load(f)
CONFIGS = _Config(**__config)

# Check the correct UI framework
if 'framework' not in CONFIGS:
    raise ValueError("The 'framework' entry is not defined in config.toml.")
if 'name' not in CONFIGS.framework:
    raise ValueError(
        "The 'name' entry is not defined in 'framework' config.toml.")
# if CONFIGS.framework.name.upper() == "KIVY":
#     try:
#         import kivy  # type: ignore # noqa
#     except ImportError:
#         raise ValueError("The config.toml files set to 'kivy'.")
# elif CONFIGS.framework.name.upper() == "TOGA":
#     try:
#         import toga  # noqa
#     except ImportError:
#         raise ValueError("The config.toml files set to 'toga'.")


class Settings(DefaultDict):
    __instance = None
    __is_changed = False
    __loading_path = ""
    FILE_NAME = "mp3Player_settings.json"
    DEFAULT_PLAYLIST_NAME = "Playlist 1"

    def __init__(__self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def load(data_path) -> Settings:
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
                    if len(Settings.__instance.Playlists) == 0:
                        Settings.__instance.Playlists.append(Dict(
                            {'name': Settings.DEFAULT_PLAYLIST_NAME,
                             'tracks': []
                             }))
                        Settings.__instance.last_playlist_private = ""
                        Settings.__is_changed = True
                    else:
                        Settings.__is_changed = False
            except FileNotFoundError:
                Path(data_path).mkdir(parents=True, exist_ok=True)
                ###################################
                # Define the default settings here
                default_conf = {'Playlists': [
                                {'name': Settings.DEFAULT_PLAYLIST_NAME,
                                 'tracks': []
                                 },
                                ],
                                'last_playlist_private': '',
                                }
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

    def has_playlist(self, name: str):
        """check playlist by its name.

        Parameters
        ----------
        name : str
            The name of the playlist to search for.

        """
        playlists = [playlist for playlist in self.Playlists
                     if playlist.name == name]
        return len(playlists) > 0

    def find_playlist(self, name: str | None) -> Dict:
        """Find playlist by its name.

        Parameters
        ----------
        name : str
            The name of the playlist to search for.

        """
        playlists = [playlist for playlist in self.Playlists
                     if playlist.name == name]
        if len(playlists) == 0:
            raise ValueError(
                f"No playlist named '{name}' is found in settings.")
        if len(playlists) > 1:
            raise ValueError(
                f"More than one playlist named '{name}' is found in settings.")
        return playlists[0]

    def search_tracks(self, playlist_name: str, name: str):
        """Search for tracks by its name in a playlist.

        Parameters
        ----------
        playlist_name : str
            The partial name of the playlist that contains.
        name : str
            The name of the track to search for.
        """
        playlist = self.find_playlist(playlist_name)
        tracks = [track for track in playlist.tracks
                  if name in track.name]
        return tracks

    def find_track(self, playlist_name: str, name: str):
        """Find track by its name in a playlist.

        Parameters
        ----------
        playlist_name : str
            The name of the playlist that contains.
        name : str
            The name of the track to search for.
        """
        playlist = self.find_playlist(playlist_name)
        tracks = [track for track in playlist.tracks
                  if track.name == name]
        if len(tracks) == 0:
            raise ValueError(
                f"No track named '{name}' is found in playlist '{playlist_name}'.")
        if len(tracks) > 1:
            raise ValueError(
                f"More than one track named '{name}' is found in playlist '{playlist_name}'.")
        return tracks[0]

    def find_next_track(self, playlist_name: str, track):
        """Find the next track in the playlist.

        Parameters
        ----------
        playlist_name : str
            The name of the playlist that contains.
        track
            The track to search for.
        """
        playlist = self.find_playlist(playlist_name)
        tracks = playlist.tracks
        index = tracks.index(track)
        if index + 1 >= len(tracks):
            return tracks[0]
        return tracks[index + 1]

    def find_previous_track(self, playlist_name: str, track):
        """Find the previous track in the playlist.

        Parameters
        ----------
        playlist_name : str
            The name of the playlist that contains.
        track
            The track to search for.
        """
        playlist = self.find_playlist(playlist_name)
        tracks = playlist.tracks
        index = tracks.index(track)
        if index - 1 < 0:
            return tracks[-1]
        return tracks[index - 1]

    def add_track(self, playlist_name: str, name: str, length: str, path: str):
        """Add a track to the playlist.

        Parameters
        ----------
        playlist_name : str
            The name of the playlist that contains.
        name : str
            The name of the track to add.
        length: str
            The length of the track to add.
        path: str
            The path of the track to add.
        """
        playlist = self.find_playlist(playlist_name)
        # Add the track to the playlist settings
        playlist.tracks.append(Dict({
            "name": name,
            "length": length,
            "path": path
        }))
        Settings.__is_changed = True

    def remove_track(self, playlist_name: str, track) -> None:
        """Remove the track from the playlist.

        Parameters
        ----------
        playlist_name : str
            The name of the playlist that contains.
        track
            The track to remove.
        """
        playlist = self.find_playlist(playlist_name)
        # Remove the track from the playlist settings
        playlist.tracks.remove(track)
        Settings.__is_changed = True

    def add_playlist(self, name: str):
        """Add a playlist to the settings.

        Parameters
        ----------
        name : str
            The name of the playlist to add.

        """
        # Add the playlist to the settings
        self.Playlists.append(Dict({
            "name": name,
            "tracks": []
        }))
        Settings.__is_changed = True

    def edit_playlist(self, name: str, new_name: str, data_path: Path):
        """Edit a playlist to the settings.

        Parameters
        ----------
        name : str
            The name of the playlist to add.

        new_name : str
            The name of the playlist to add.

        data_path: Path
            The path of the data folder.
        """
        playlist = self.find_playlist(name)
        dir_old_path = data_path / "files" / playlist.name.replace(" ", "")
        playlist.name = new_name
        dir_new_path = data_path / "files" / playlist.name.replace(" ", "")
        if os.path.exists(dir_old_path):
            # Rename the directory and its contents
            shutil.move(dir_old_path, dir_new_path)
            for track in playlist.tracks:
                track.path = str(dir_new_path / Path(track.path).name)
        Settings.__is_changed = True

    def remove_playlist(self, name: str, data_path: Path):
        """Remove a playlist from the settings.

        Parameters
        ----------
        name : str
            The name of the playlist to remove.

        data_path: Path
            The path of the data folder.
        """
        # Remove the playlist from the settings
        playlist = self.find_playlist(name)
        self.Playlists.remove(playlist)
        dir_path = data_path / "files" / playlist.name.replace(" ", "")
        if os.path.exists(dir_path):
            # Remove the directory and its contents
            shutil.rmtree(dir_path)
        Settings.__is_changed = True

    def get_last_playlist(self) -> str:
        """Return the last playlist name.

        Returns
        -------
        str
            The last playlist name.
        """
        ret = self.last_playlist_private
        if ret == "" or ret == {}:
            if len(self.Playlists) == 0:
                # If the attribute is not set, return the default value
                self.add_playlist(Settings.DEFAULT_PLAYLIST_NAME)
                self.save()

            # If the attribute is not set, return the default value
            # self.last_playlist_private = self.Playlists[0].name
            return self.Playlists[0].name

        if ret not in [p.name for p in self.Playlists]:
            if len(self.Playlists) == 0:
                # If the attribute is not set, return the default value
                self.add_playlist(Settings.DEFAULT_PLAYLIST_NAME)
                self.save()

            # If the attribute is not set, return the default value
            # self.last_playlist_private = self.Playlists[0].name
            return self.Playlists[0].name

        return ret

    def set_last_playlist(self, name: str):
        """Set the last playlist name.

        Parameters
        ----------
        name : str
            The name of the playlist to set as last.
        """
        self.last_playlist_private = name
        Settings.__is_changed = True


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
