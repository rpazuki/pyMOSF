import logging
from enum import Enum
from pathlib import Path
from typing import Any

from rubicon.objc import ObjCClass, ObjCProtocol, objc_block, objc_method, py_from_ns
from rubicon.objc.runtime import objc_id

import pyMOSF.core as core
from pyMOSF.core import safe_async_call

log = logging.getLogger(__name__)

# Import necessary UIKit classes
UIImagePickerController = ObjCClass("UIImagePickerController")
UIApplication = ObjCClass("UIApplication")
NSObject = ObjCClass("NSObject")
UIViewController = ObjCClass("UIViewController")
UIImagePickerControllerDelegate = ObjCProtocol(
    "UIImagePickerControllerDelegate")
UINavigationControllerDelegate = ObjCProtocol("UINavigationControllerDelegate")


class ImagePickerReturn(int, Enum):
    All = 0  # returns all the informations from the picker
    PATH = 1  # returns the path of the selected file
    IMAGE = 2  # returns the image data


class PhotoPickerDelegate(NSObject,  # type: ignore
                          protocols=[UIImagePickerControllerDelegate,  # type: ignore
                                     UINavigationControllerDelegate]):  # type: ignore

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
    def imagePickerController_didFinishPickingMediaWithInfo_(self,
                                                             picker: objc_id,
                                                             info: objc_id) -> None:
        # Handle the selected photo
        if self.serviceCallback is not None:
            self.serviceCallback(info)  # type: ignore
        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.dismissViewControllerAnimated_completion_(
            True, None)

    @objc_method
    def imagePickerControllerDidCancel_(self, picker: objc_id) -> None:
        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.dismissViewControllerAnimated_completion_(
            True, None)


class IOSPhotoPicker(core.AsyncService):
    def __init__(self, imagePickerReturn: ImagePickerReturn = ImagePickerReturn.IMAGE) -> None:
        super().__init__()
        # IMPORTANT: the delegate must be created and stored here
        # because the delegate is a weak reference
        # and can be deleted without any reference in Python side
        self.delegate = PhotoPickerDelegate.alloc().init_()
        self.imagePickerReturn = imagePickerReturn

    @safe_async_call(log)
    async def handle_event(self,
                           widget: Any,
                           app,
                           service_callback,
                           *args, **kwargs):
        if service_callback is None:
            raise ValueError("service_callback must be provided")

        picker = UIImagePickerController.alloc().init()  # type: ignore
        picker.sourceType = 0  # 0 = Photo Library

        def local_callback(info_c: objc_id) -> None:
            # Convert the NSDictionary to a Python dictionary
            info_dict: dict | Any = py_from_ns(info_c)
            photo_dict = {}
            info_dict: dict | Any = py_from_ns(info_c)

            match self.imagePickerReturn:
                case ImagePickerReturn.All:
                    photo_dict = {}
                    for key, value in info_dict.items():
                        key_str: str | Any = py_from_ns(key)
                        photo_dict[key_str] = py_from_ns(value)
                    service_callback(photo_dict)
                    return
                case ImagePickerReturn.PATH:
                    for key, value in info_dict.items():
                        if py_from_ns(key) == "UIImagePickerControllerImageURL":
                            path_str: str = py_from_ns(
                                value.path)  # type: ignore
                            service_callback(Path(path_str))
                            return
                case ImagePickerReturn.IMAGE:
                    # new version of swift sugests to use pngData()
                    # But obejective-c still uses UIImagePNGRepresentation
                    # So, I directly load the imapge from the URL
                    # from rubicon.objc.runtime import load_library
                    # uiKit = load_library("UIKit")
                    # for key, value in info_dict.items():
                    #     if py_from_ns(key) == "UIImagePickerControllerOriginalImage":
                    #     png = uiKit.UIImagePNGRepresentation(
                    #         value)  # type: ignore
                    #     from PIL import Image
                    #     service_callback( Image.open(io.BytesIO(png)))
                    #     return
                    path_str = ""
                    # file = None
                    for key, value in info_dict.items():
                        if py_from_ns(key) == "UIImagePickerControllerImageURL":
                            path_str: str = py_from_ns(
                                value.path)  # type: ignore
                        # if py_from_ns(key) == "UIImagePickerControllerOriginalImage":
                        #     file = value
                    if path_str != "":
                        from PIL import Image

                        # file.startAccessingSecurityScopedResource()
                        img = Image.open(Path(path_str))
                        # file.stopAccessingSecurityScopedResource()
                        service_callback(img)
                        return

                    # Set the service callback
        self.delegate.set_serviceCallback(local_callback)  # type: ignore
        # Set the delegate
        picker.delegate = self.delegate
        # Present the photo picker
        keyWindow = UIApplication.sharedApplication.keyWindow  # type: ignore
        keyWindow.rootViewController.presentViewController_animated_completion_(
            picker, True, None)
