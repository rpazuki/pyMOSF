import logging
import os

import kivy
from kivy.lang import Builder  # type: ignore
from kivy.logger import Logger  # type: ignore

from pyMOSF.kivy import KivyMultiLayoutApp  # , Layout
from pyMOSF.templates.kivy.example_layouts import ExampleViewLayout

logging.root = Logger

kivy.require('1.8.0')  # type: ignore
log = logging.getLogger(__name__)


class KivyApp(KivyMultiLayoutApp):
    def __init__(self, **kwargs):
        #
        self.main_layout = ExampleViewLayout(self)
        super(KivyApp, self).__init__(
            init_layout=self.main_layout,
            **kwargs)
        self.layout = self.main_layout

    def show_main(self):
        self.show_layout(self.main_layout)


def create_app():
    log.info("Example app stars")
    app = KivyApp()
    return app


if __name__ == '__main__':
    # This main entry point is used for debugging.
    # It is not used in the main app.
    log.info("Debug main is called.")
    Builder.load_file(os.path.abspath(
        "pyMOSF/templates/kivy/example_layouts.kv"))
    log.info("KV is loaded.")
    create_app().run()
