from abc import abstractmethod
from typing import Any

from numpy import ndarray

import pyMOSF.core as core
from pyMOSF.config import Dict
from pyMOSF.core.pipelines import Process


class ToOpenCVImageProcess(Process):
    @abstractmethod
    def __call__(self, *, image: ndarray, **kwargs) -> Dict:
        pass


class ToFrameworkImageProcess(Process):
    @abstractmethod
    def __call__(self, *, image: Any, **kwargs) -> Dict:
        pass


class ProcessesRegistry(object):
    """A singleton object that store Framework specific Process.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessesRegistry, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance
    processes = {}

    def __getitem__(self, key):
        return self.processes[key]

    def __setitem__(self, key, newvalue):
        self.processes[key] = newvalue


class SyncImageService(core.SyncService):
    def __init__(self) -> None:
        registry = ProcessesRegistry()
        self.toOpenCV = registry[ToOpenCVImageProcess]
        self.toFramework = registry[ToFrameworkImageProcess]


class AsyncImageService(core.AsyncService):
    def __init__(self) -> None:
        registry = ProcessesRegistry()
        self.toOpenCV = registry[ToOpenCVImageProcess]
        self.toFramework = registry[ToFrameworkImageProcess]
