"""
Studying bees diseases by analysing photos
"""
import logging

from pyMOSF.templates.toga.example_layouts import ExampleViewLayout
from pyMOSF.toga import TogaMultiLayoutApp

log = logging.getLogger(__name__)


class TogaApp(TogaMultiLayoutApp):
    """A toga App class that has a layout.

    The layout class will create UI elements and its main_box will be added
    as the app main window's content.
    """

    def __init__(self,
                 formal_name: str,
                 app_id="net.pazuki.torchApp"):

        self.layout = ExampleViewLayout(self)

        super(TogaApp, self).__init__(init_layout=self.layout,
                                      formal_name=formal_name,
                                      app_id=app_id,
                                      )

    def startup(self):
        super().startup()
        self.show_layout(self.layout)


def create_app():
    log.info("Eample app stars")

    app = TogaApp("Example app")
    return app


if __name__ == "__main__":
    # This main entry point is used for debugging.
    # It is not used in the main app.
    log.info("Debug main is called.")
    try:
        create_app().main_loop()
    except Exception as e:
        print(e)
        log.error("Exception in main loop. \n"
                  f"Exception: {e}"
                  f"\nTraceback: {e.__traceback__}")
