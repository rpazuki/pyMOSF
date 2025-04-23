import logging
import os
from pathlib import Path

is_not_kivy = True
try:
    from kivy.logger import Logger  # type: ignore
    logging.root = Logger
    root = logging.getLogger().root
    is_not_kivy = False
except ImportError:
    root = logging.getLogger().root


class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, ei):
        result = super().formatException(ei)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


def std_out_log(log_level="INFO",
                LOGGER_FORMAT=logging.BASIC_FORMAT):
    handler = logging.StreamHandler()
    # LOGGER_FORMAT = "%(levelname)s:%(name)s:%(message)s \n %(pathname)s @ %(lineno)d"
    # LOGGER_FORMAT = "%(levelname)s:%(name)s:%(message)s (in %(filename)s @ line %(lineno)d)"
    formatter = OneLineExceptionFormatter(LOGGER_FORMAT)
    handler.setFormatter(formatter)
    # root = logging.getLogger()
    root.setLevel(os.environ.get("LOGLEVEL", log_level))
    if is_not_kivy:
        root.addHandler(handler)


def file_out_log(path,
                 log_level="INFO",
                 LOGGER_FORMAT="%(levelname)s:%(asctime)s:%(name)s:%(message)s"):
    import logging.handlers

    # from logging.handlers import RotatingFileHandler
    # handler = RotatingFileHandler(os.environ.get("LOGFILE", path),
    #                               maxBytes=10000,
    #                               backupCount=3)
    if not os.path.exists(path):
        try:
            file_path = os.environ.get("LOGFILE", path)
            with open(file_path, 'w') as file:
                file.write("")
        except FileNotFoundError:
            file_path = os.environ.get("LOGFILE", path)
            directories, _ = os.path.split(file_path)
            Path(directories).mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.WatchedFileHandler(
        os.environ.get("LOGFILE", path))
    # LOGGER_FORMAT = logging.BASIC_FORMAT
    # LOGGER_FORMAT = "%(levelname)s:%(name)s:%(message)s \n %(pathname)s @ %(lineno)d"
    # LOGGER_FORMAT = "%(levelname)s:%(name)s:%(message)s (in %(filename)s @ line %(lineno)d)"
    formatter = logging.Formatter(LOGGER_FORMAT)
    handler.setFormatter(formatter)
    # root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(os.environ.get("LOGLEVEL", log_level))


def __dummy__():
    pass


if __name__ == "__main__":
    std_out_log()
