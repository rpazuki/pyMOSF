import logging
import shutil
from pathlib import Path
from typing import Any

from rubicon.objc import (
    ObjCClass,
    ObjCProtocol,
    objc_block,
    objc_const,
    objc_method,
    py_from_ns,
)
from rubicon.objc.runtime import Foundation, load_library, objc_id

import pyMOSF.core as core
from pyMOSF.config import Dict
from pyMOSF.core import safe_async_call

log = logging.getLogger(__name__)

# Import necessary UIKit classes
UIDocumentPickerViewController = ObjCClass("UIDocumentPickerViewController")
UIApplication = ObjCClass("UIApplication")
NSObject = ObjCClass("NSObject")
UIViewController = ObjCClass("UIViewController")
UIDocumentPickerDelegate = ObjCProtocol("UIDocumentPickerDelegate")
NSURL = ObjCClass("NSURL")
NSString = ObjCClass("NSString")
NSNotificationCenter = ObjCClass('NSNotificationCenter')
NSLOG = Foundation.NSLog

NSFileManager = ObjCClass('NSFileManager')


class DocumentPickerDelegate(NSObject,  # type: ignore
                             protocols=[UIDocumentPickerDelegate]):  # type: ignore

    @objc_method
    def init_(self):
        self = self.init()
        if self is None:
            return None
        self.serviceCallback = None
        return self

    @objc_method
    def set_serviceCallback(self, serviceCallback: objc_block):
        self.serviceCallback = serviceCallback

    @objc_method
    def get_serviceCallback(self):
        return self.serviceCallback

    @objc_method
    def documentPicker_didPickDocumentsAtURLs_(self, picker: objc_id, urls: objc_id) -> None:
        # Handle the selected files
        if self.serviceCallback is not None:
            self.serviceCallback(urls)  # type: ignore

        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.dismissViewControllerAnimated_completion_(
            True, None)

    @objc_method
    def documentPickerWasCancelled_(self, picker: objc_id) -> None:
        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.dismissViewControllerAnimated_completion_(
            True, None)


class IOSFileOpen(core.AsyncService):
    def __init__(self,
                 initial_directory: Path,
                 file_types: list[str] = ["UTTypeData"],
                 multiple_select: bool = True,
                 ) -> None:
        super().__init__()
        # IMPORTANT: the delegate must be create and store here
        # because the delegate is a weak reference
        # and can be deleted without any reference in Python side
        self.delegate = DocumentPickerDelegate.alloc().init_()
        self.temp_path = initial_directory
        self.document_types = file_types
        self.allowsMultipleSelection = multiple_select
        self.libcf = load_library("UniformTypeIdentifiers")

    @safe_async_call(log)
    async def handle_event(self,
                           widget: Any,
                           app,
                           service_callback,
                           *args, **kwargs):
        if service_callback is None:
            raise ValueError("service_callback must be provided")

        # You can specify other UTIs if needed
        document_types = [objc_const(self.libcf, item)
                          for item in self.document_types]
        picker = UIDocumentPickerViewController.alloc()  # type: ignore
        picker = picker.initForOpeningContentTypes_(
            document_types)
        picker.allowsMultipleSelection = self.allowsMultipleSelection

        def local_callback(fnames_c: objc_id) -> None:
            # convert the NSArray to a Python list
            fnames_c_list = py_from_ns(fnames_c)
            fnames = []
            for item in fnames_c_list:  # type: ignore
                # All files are copied to local sandbox , before
                # the service caller's callback is called.
                # Therefore, all paths are updated accordingly
                # This steps must happen between a SecurityScope block
                item.startAccessingSecurityScopedResource()
                path_str: str = py_from_ns(item.path)  # type: ignore
                f_src = open(path_str, 'rb')
                dest_path = self.temp_path / Path(path_str).name
                f_dest = open(dest_path, 'wb')
                shutil.copyfileobj(f_src, f_dest)
                item.stopAccessingSecurityScopedResource()
                # store the converted Path object
                fnames.append(dest_path)

            if self.allowsMultipleSelection:
                service_callback(Dict(files=fnames))
            else:
                if len(fnames) > 0:
                    service_callback(Dict(file=fnames[0]))
        # Set the service callback
        self.delegate.set_serviceCallback(local_callback)  # type: ignore
        # Set the delegate
        picker.delegate = self.delegate
        # Present the document picker
        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.presentViewController_animated_completion_(
            picker, True,  None)
