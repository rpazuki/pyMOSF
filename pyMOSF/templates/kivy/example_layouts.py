from __future__ import annotations

import logging

from kivy.uix.label import Label  # type: ignore

from pyMOSF.core import Event, EventType, ServiceRegistry
from pyMOSF.kivy import KivyComponent, KivyMultiLayoutApp, KivyStackedLayout
from pyMOSF.kivy.services.io import FileOpen

# from pathlib import Path


log = logging.getLogger(__name__)

TOOLBAR_HEIGHT = 125


# Builder.load_file(str(Path("layout.kv").resolve()))

class ToolbarComponent(KivyComponent):
    @property
    def label(self):
        return self.ids.label

    @property
    def parent_layout(self) -> ExampleViewLayout:
        return self._layout  # type: ignore

    def button_pressed(self):
        self.parent_layout.button_pressed()  # type: ignore

    def file_selected(self, paths):
        self.parent_layout.file_opened(paths.file)  # type: ignore

    def _non_ios_config(self):
        ServiceRegistry().bind_event(
            Event("open_file",
                  EventType.ON_PRESS,
                  FileOpen(dialog_title="Open file",
                           multiple_select=False),
                  service_callback=self.file_selected))

    def on_linux_config(self):
        self._non_ios_config()

    def on_windows_config(self):
        self._non_ios_config()

    def on_darwin_config(self):
        self._non_ios_config()

    def _ios_config(self):
        # Load the library inside the functoin
        # to avoid dependency problem on other platform
        from pyMOSF.services.open_file_ios import IOSFileOpen
        ServiceRegistry().bind_event(
            Event("open_file",
                  EventType.ON_PRESS,
                  IOSFileOpen(initial_directory=self.ml_app.data_path,
                              multiple_select=False),
                  service_callback=self.file_selected))

    def on_ios_config(self):
        self._ios_config()

    def on_ipados_config(self):
        self._ios_config()


class TextViewComponent(KivyComponent):

    @property
    def label(self) -> Label:
        return self.ids.label


class ExampleViewLayout(KivyStackedLayout):
    def __init__(self, app: KivyMultiLayoutApp):
        super().__init__(app,
                         ToolbarComponent,
                         TextViewComponent)

        self.counter = 1

    @property
    def files_toolbar(self) -> ToolbarComponent:
        return self[ToolbarComponent]

    @property
    def label_view(self) -> Label:
        if self[TextViewComponent] is None:
            raise ValueError("Main box has not been initialized.")
        return self[TextViewComponent].label

    def on_common_config(self):
        ############
        # Settings
        self.settings = self.ml_app.settings

    def on_load(self):
        return super().on_load()

    def button_pressed(self):
        self.label_view.text = f"Button pressed {self.counter} times."
        self.counter += 1

    def file_opened(self, file: str):   # type: ignore
        self.label_view.text = f"File opened: \n{file}"
