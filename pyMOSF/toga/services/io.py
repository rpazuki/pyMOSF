import logging
from pathlib import Path
from typing import Any

import toga

import pyMOSF.core as core
from pyMOSF.config import Dict
from pyMOSF.core import safe_async_call

log = logging.getLogger(__name__)


class FileOpen(core.AsyncService):
    def __init__(self,
                 dialog_title: str = "Open file",
                 initial_directory: Path | str | None = None,
                 file_types: list[str] | None = None,
                 multiple_select: bool = False) -> None:
        super().__init__()
        self.dialog_title = dialog_title
        self.initial_directory = initial_directory
        self.file_types = file_types
        self.multiple_select = multiple_select

    @safe_async_call(log)
    async def handle_event(self,
                           widget: Any,
                           app,
                           service_callback=None,
                           *args, **kwargs):

        fname = await widget.app.dialog(
            toga.OpenFileDialog(title=self.dialog_title,
                                initial_directory=self.initial_directory,
                                file_types=self.file_types,
                                multiple_select=self.multiple_select))
        if fname is None:
            return  # No file selected
        if service_callback is not None:
            if self.multiple_select:
                # If multiple files are selected, return a list of file names
                service_callback(Dict(files=fname))
            else:
                service_callback(Dict(file=fname))
        return
