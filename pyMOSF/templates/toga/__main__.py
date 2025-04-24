
import logging

from .app import create_app as create_toga_app

log = logging.getLogger(__name__)

if __name__ == "__main__":
    log.info("main is called.")
    try:
        create_toga_app().main_loop()
    except Exception as e:
        print(e)
        log.error("Exception in main loop. \n"
                  f"Exception: {e}"
                  f"\nTraceback: {e.__traceback__}")
