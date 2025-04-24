import logging
import os
from pathlib import Path
from typing import Any, Callable

from kivy.factory import Factory  # type: ignore
from kivy.lang import Builder  # type: ignore

# import toga
from kivy.properties import ObjectProperty  # type: ignore
from kivy.uix.floatlayout import FloatLayout  # type: ignore
from kivy.uix.popup import Popup  # type: ignore

import pyMOSF.core as core
from pyMOSF.config import Dict
from pyMOSF.core import safe_call

log = logging.getLogger(__name__)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


Factory.register('LoadDialog', cls=LoadDialog)
Builder.load_string('''
<LoadDialog>:
    BoxLayout:
        size: root.size
        pos: root.pos
        orientation: "vertical"
        FileChooserIconView:
            id: filechooser

        BoxLayout:
            size_hint_y: None
            height: 30
            Button:
                text: "Cancel"
                on_release: root.cancel()

            Button:
                text: "Load"
                on_release: root.load(filechooser.path, filechooser.selection)
                    ''')


class FileOpen(core.SyncService):
    def __init__(self,
                 dialog_title: str = "Open file",
                 initial_directory: Path | str | None = None,
                 file_types: list[str] | None = None,
                 multiple_select: bool = False) -> None:
        super().__init__()
        self.app = None
        self.dialog_title = dialog_title
        self.initial_directory = initial_directory
        self.file_types = file_types
        self.multiple_select = multiple_select

    def dismiss_popup(self):
        self._popup.dismiss()

    @safe_call(log)
    def load(self, path, filename):
        if len(filename) > 0:
            if self.service_callback is not None:
                if self.multiple_select:
                    # If multiple files are selected, return a list of file names
                    self.service_callback(Dict(files=filename))
                else:
                    # If only one file is selected, return the file name
                    self.service_callback(Dict(file=filename[0]))
        self._popup.dismiss()

    @safe_call(log)
    def handle_event(self,
                     widget: Any,
                     app: core.AbstractApp,
                     service_callback: Callable | None = None,
                     *args,
                     **kwargs):

        self.app = app
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        if self.initial_directory is None:
            content.ids['filechooser'].path = os.getcwd()
        else:
            content.ids['filechooser'].path = str(self.initial_directory)
        if self.file_types is not None:
            content.ids['filechooser'].filters = self.file_types
        content.ids['filechooser'].multiselect = self.multiple_select
        self._popup = Popup(title=self.dialog_title, content=content,
                            size_hint=(0.9, 0.9))
        self.service_callback = service_callback
        self._popup.open()
        return
