"""
 Life-cycle sequence:
1- KivyMultiLayoutApp.__init__ : manager, _layout_lookup, _screen_lookup
    1-1- AbstractApp.__init__ : _settings, layout

2- KivyStackedLayout.__init__  : types, _instances
    2-1- KivyLayout.__init__ : _main_box
        2-1-1- AbstractLayout.__init__ : _app


3-KivyMultiLayoutApp.build : main_window
    3-1- main_window.add_widget(self._current_layout.main_box)
    3-2- manager.add_widget(self.main_window)
    3-3- AbstractApp.on_begin :
        3-3-1- AbstractApp._set_config :
        3-3-2- AbstractApp.on_load :
            3-3-2-1- AbstractLayout.build_layout -> root :
                3-3-2-1-1- Layout[Box]._build_box -> _box
                    3-3-2-1-1-1- Layout[Box]._build_box
                        3-3-2-1-1-1-1- KivyLayout._build_box :  create box and return

                    or alternativly

                    3-3-2-1-1-1- StackedLayout[Box, *Ts].build_layout
                        3-3-2-1-1-1-1 StackedLayout[Box, *Ts]._build_box
                            3-3-2-1-1-1-1-1 Component[Box, *Ts]._init_
                                3-3-2-1-1-1-1-1-1- KivyComponent._init_: layout, add ids
                        3-3-2-1-1-1-2 self._add_to_main_box(self._box, component)
                        3-3-2-1-1-1-3 _get_component_passthrough
                        3-3-2-1-1-1-4 Component[Box, *Ts].on_load

            3-3-2-2- AbstractApp.__enumerate_elements(root) :
            3-3-2-3- AbstractLayout._set_config :
            3-3-2-4- Register Services of 'root'
            3-3-2-5- AbstractLayout.on_load :
    3-4- self._add_layout(self._current_layout)

"""

from __future__ import annotations

import logging
from pathlib import Path

from kivy.app import App as kivyApp  # type: ignore #

# from kivy.core.window import Window  # type: ignore
from kivy.uix.boxlayout import BoxLayout  # type: ignore
from kivy.uix.screenmanager import Screen, ScreenManager  # type: ignore

from pyMOSF.config import Configurable, GUIFramework, Settings
from pyMOSF.core import (
    Component,
    Layout,
    MultiLayoutApp,
    ServiceRegistry,
    StackedLayout,
)

ServiceRegistry._framework = GUIFramework.KIVY

log = logging.getLogger(__name__)


class KivyLayout(Layout):
    def __init__(self, app: KivyMultiLayoutApp) -> None:
        super().__init__(app)
        self._app = app

    @property
    def ids(self):
        if self._box is None:
            raise ValueError("box has not been initialized (_build_box).")
        return self._box.ids

    @property
    def ml_app(self) -> KivyMultiLayoutApp:
        return self._app


class KivyBox(BoxLayout):
    """This class is used for element inkv files"""

    def __init__(self, layout: KivyLayout, **kwargs) -> None:
        super().__init__(**kwargs)
        self._layout = layout
        for key in self.ids:
            setattr(self.ids[key], "id", key)

    @property
    def ml_app(self) -> KivyMultiLayoutApp:
        return self._layout.ml_app

    @property
    def parrent_layout(self) -> KivyLayout:
        return self._layout


class KivyComponent(Component, Configurable, BoxLayout):
    def __init__(self, layout: KivyStackedLayout, **kwargs) -> None:
        super().__init__(layout, **kwargs)
        self._layout = layout
        for key in self.ids:
            setattr(self.ids[key], "id", key)

    @property
    def ml_app(self) -> KivyMultiLayoutApp:
        return self._layout.ml_app

    @property
    def parrent_layout(self) -> KivyStackedLayout:
        return self._layout


class KivyStackedLayout(StackedLayout):

    def __init__(self,
                 app: KivyMultiLayoutApp,
                 *types):  # type: ignore
        self._main_container = BoxLayout()
        self._main_container.orientation = 'vertical'
        super().__init__(app, self._main_container, *types)

    @property
    def ml_app(self) -> KivyMultiLayoutApp:
        if self._app is None:
            raise ValueError("app has not been initialized.")
        return self._app

    @ml_app.setter
    def ml_app(self, value: KivyMultiLayoutApp):
        self._app = value

    def _add_to_main_box(self, box: BoxLayout, element: BoxLayout):
        box.add_widget(element)


class KivyMultiLayoutApp(MultiLayoutApp, kivyApp):
    def __init__(self,
                 init_layout: KivyLayout | KivyStackedLayout,
                 settings: Settings | None = None,
                 **kwargs) -> None:
        self._main_container = BoxLayout()
        self._main_container.orientation = 'vertical'
        self.manager = ScreenManager()
        self._screen_lookup = {}
        self._current_layout = init_layout
        super().__init__(self._main_container, init_layout, settings, **kwargs)

    @property
    def path(self):
        return Path(self.directory)  # type: ignore

    @property
    def data_path(self):
        return Path(self.user_data_dir)  # type: ignore

    @property
    def current_layout(self) -> KivyLayout | KivyStackedLayout:
        return self._current_layout

    def _add_layout(self, layout: KivyLayout | KivyStackedLayout):
        if layout._name not in self._screen_lookup:
            self.main_window: Screen = Screen(name=layout._name)
            self._screen_lookup[layout._name] = self.main_window
            self.main_window.add_widget(self.layout.main_box)
            self.manager.add_widget(self.main_window)
            self.manager.current = layout._name
        else:
            self.manager.current = layout._name

    def build(self):
        """Construct and show the Kivy application (it's called by kivy app).

        It also call the layout build and bind the serivices handlers
        to UI elements on_press call back, if their ids correspond to
        an id in ServiceRegistry.
        """
        self.main_window: Screen = Screen(name=self.layout._name)
        self._screen_lookup[self.layout._name] = self.main_window
        self.main_window.add_widget(self._current_layout.main_box)
        self.manager.add_widget(self.main_window)
        # Call on_load in AbstractApp to register the event once
        self.on_begin()
        # It calls once
        self._add_layout(self._current_layout)
        #
        return self.manager

    def on_stop(self):
        """Alrert layout and its components the end of app cycle (it's called by kivy app)."
        """
        self.on_end()  # self.layout.on_end() will be called here
        return super().on_stop()
