"""The core module of toga related implimentation.

   Notes:
   ------
   Configurable
       1- All three AbstractApp (TogaMultiLayoutApp),
          AbstractLayout (TogaLayout) and TogaComponent
          are 'Configurable'. So, they can implement
          os dependent configuration.
        2- AbstractApp calls Configurable's _set_config once in its
           lifcycle:  on_begin() -- for TogaMultiLayoutApp
           it happens in startup.
        3- AbstractLayout (TogaLayout) calls 'Configurable' once on its
           first load: on_load -- for TogaLayout, it is called
           on 'show_layout' of the app.
        4- AbstractLayout (TogaLayout) are created once, but will be used agian
           in TogaMultiLayoutApp's 'show_layout'. So, their
           configuration will happens only once. However, the
           AbstractLayout's 'on_load' function will be call everytime
           that it is loaeded again.
        5- TogaComponent's 'Configurable' are called once by the
           time their layout 'Configurable' are called.

   TogaStackedLayout (TogaLayout)
       1- It can have one or more TogaComponents. It is just need
          the class names of the TogaComponents in its constructor.
       2- Each component is accessible by its class name in the
          layout: e.g. layout[TogaComponentClass].
       3- It is possible to directly access the component method by
          decorating them with '@component_method'. Aftre that, we
          can call them, e.g., like layout.component_function().
          If it is not decorated. it can riase 'ServiceArgumentError'
          exception when thery are used for services argument.

   TogaComponent
       1- They must implement all thier UI elements inside
          __init__ and pass it to its super argument, after their
          parent layout.
       2- To make any of its method directly accessible in their
          layout, we can use '@component_method' decorator.
          If it is not decorated. it can riase 'ServiceArgumentError'
          exception when they are used for services argument.
"""
from __future__ import annotations

import logging

import toga
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN  # type: ignore

from pyMOSF.config import Configurable, GUIFramework, Settings
from pyMOSF.core import (
    Component,
    Layout,
    MultiLayoutApp,
    ServiceRegistry,
    StackedLayout,
)

ServiceRegistry._framework = GUIFramework.TOGA


log = logging.getLogger(__name__)


class Promiseable:
    def __init__(self, **kwargs) -> None:
        super().__init__()

    @property
    def ml_app(self) -> TogaMultiLayoutApp:
        if self._app is None:
            raise ValueError("app has not been initialized.")
        return self._app

    @ml_app.setter
    def ml_app(self, value: TogaMultiLayoutApp):
        self._app = value

    def promise(self, func):
        if not callable(func):
            raise ValueError("The argument must be callable. "
                             "(Turn it into a lambda if it's a statment.)")

        def wrapper():
            func()

        self.ml_app.loop.call_soon_threadsafe(wrapper)


class TogaLayout(Layout, Promiseable):
    def __init__(self, app: TogaMultiLayoutApp) -> None:
        self._app = app
        super().__init__(app)

    @property
    def ml_app(self) -> TogaMultiLayoutApp:
        if self._app is None:
            raise ValueError("app has not been initialized.")
        return self._app


class TogaComponent(Component, Configurable, toga.Box, Promiseable):
    def __init__(self, layout: TogaStackedLayout, **kwargs) -> None:
        self._layout = layout
        super().__init__(layout, **kwargs)

    @property
    def ml_app(self) -> TogaMultiLayoutApp:
        if self._layout.ml_app is None:
            raise ValueError("app has not been initialized.")
        return self._layout.ml_app

    @property
    def parent_layout(self) -> TogaStackedLayout:
        return self._layout


class TogaStackedLayout(StackedLayout, Promiseable):
    def __init__(self,
                 app: TogaMultiLayoutApp,
                 *types):  # type: ignore
        self._box = toga.Box(style=Pack(direction=COLUMN,
                                        alignment=CENTER, flex=1)
                             )
        self._app = app
        super().__init__(app, self._box, *types)

    @property
    def ml_app(self) -> TogaMultiLayoutApp:
        if self._app is None:
            raise ValueError("app has not been initialized.")
        return self._app

    @ml_app.setter
    def ml_app(self, value: TogaMultiLayoutApp):
        self._app = value

    def _add_to_main_box(self, box: toga.Box, element: toga.Box):
        box.add(element)


class TogaMultiLayoutApp(MultiLayoutApp, toga.App):
    def __init__(self,
                 init_layout: TogaLayout | TogaStackedLayout,
                 settings: Settings | None = None,
                 **kwargs) -> None:
        self._main_container = toga.Box(
            style=Pack(direction=COLUMN, alignment=CENTER, flex=1)
        )
        self._current_layout = init_layout
        super().__init__(self._main_container, init_layout, settings, **kwargs)

    @property
    def path(self):
        return self.paths.app  # type: ignore

    @property
    def data_path(self):
        return self.paths.data  # type: ignore

    @property
    def current_layout(self) -> TogaLayout | TogaStackedLayout:
        return self._current_layout

    def _add_layout(self, layout: TogaLayout | TogaStackedLayout):
        self._main_container.clear()
        self._main_container.add(layout.main_box)

    def startup(self):
        """Construct and show the Toga application (it's called by toga app).

        It also call the layout build and bind the serivices handlers
        to UI elements on_press call back, if their ids correspond to
        an id in ServiceRegistry.
        """
        self.commands.clear()
        # self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window: toga.Window = toga.Window()
        self.main_window.content = self._main_container
        # Call on_load in AbstractApp to register the event once
        self.on_begin()
        # It calls once
        self._add_layout(self._current_layout)
        #
        self.main_window.show()  # type: ignore

    def on_exit(self) -> bool:
        return super().on_end()
