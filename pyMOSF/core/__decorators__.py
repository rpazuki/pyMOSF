import functools
from typing import Any, Callable

from pyMOSF.config import Dict
from pyMOSF.core import EventType
from pyMOSF.core.pipelines import (
    AbstractProcess,
    ProcessFactory,
    ProcessLogic,
    ProcessLogicProperty,
)


def component_method(func: Callable) -> Callable[..., Any]:
    """A decorator for making component's method available to layout.

       It do nothing and just annotate a class function.

       Example:
       --------
       class ExampleComponent(TogaComponent):
           @component_method
           def is_bw(self):
               return self.swt_black_white.value

           @property
           def is_gray(self):
               return self.swt_gray.value

        then, the layout that contains the 'ExampleComponent'
        can access 'is_bw' function simply like self.is_bw()

        However, for properties, you need to use the getitem
        self[ExampleComponent].is_gray

    """
    return func


# def service_callback(func):
#     """Decorate the method that as a callback that can be set as an argument.
#     """
#     def callable_func(*args_local):
#         if len(args_local) == 0:  # ordinary function
#             return func

#         def wraper(*args, **kwargs):  # object methods
#             func(args_local[0], *args, **kwargs)
#         return wraper
#     return callable_func


def silence_crossed_events(eventType: EventType, element1,  element2):
    """Silence the circular events calls between two elements.

       When a value of the second element is changed by event handler of the first one,
       such that this change fires the same event in the second one, we get a circular
       event from the second. This method let us to disble it.
    """
    _silence(element1, eventType, element2)
    _silence(element2, eventType, element1)


def _silence(element, eventType: EventType, second_element):
    try:
        import toga  # noqa
    except ImportError:
        raise NotImplementedError("This function is only available for Toga.")
    eventName = eventType.name.lower()
    # The element's event that is supposed to be called
    event = getattr(element, f"_{eventName}")
    # Decorator for the element's event that is supposed to be called

    def decorator(widget,  *args):
        # Temporarily store and disable the second element's event
        stored = getattr(second_element, f"_{eventName}")
        setattr(second_element, eventName, None)
        # call the original event handler
        event(widget,  *args)
        # Set back the second element's event
        setattr(second_element, eventName, stored)
    # reroute the element's event handler to the decorator
    setattr(element, eventName, decorator)


def processLogic(func: Callable[..., Dict]) -> Callable[..., ProcessLogic]:
    """A decorator for creating inline process.

       It can turn a function to a process, as long as the function
       arguments include '**kwargs' and returns a Dict as it payloads.
       In short, decorating a function can turn it into an inline definition
       of a process, which can be joined (>>) or forked (*) by other processes.

       Example:
           @processLogic
           def proc2(condition:bool, **kwargs) -> Dict:
               if condition:
                   return Dict(value=True)
               else:
                   return Dict(value=False)

            proc1 >> proc2()

    Parameters
    ----------
    func : Callable[..., Dict]
        Callable function that contains the logic of creating the process.
        The Callable function must include '**kwargs' in its arguments and
        returns a Dict as it payloads.

    Returns
    -------
    Callable[..., ProcessLogic]
        The decorated process. By calling it without any argument,
        it returns a process that can be joined or forked to others.
    """
    p_logic = ProcessLogic(func)

    def logic() -> ProcessLogic:
        return p_logic
    return logic


def processLogicProperty(func: Callable[..., Dict]) -> property:
    """A decorator for creating inline process inside classes as a property.

       It can turn a class method to a process as a property, as long as the method
       arguments includes '**kwargs' and returns a Dict as it payloads.
       In short, decorating a class method turns it into an inline definition
       of a process, which can be joined (>>) or forked (*) by other processes.

       Example:
           class ClassExample:
               @processLogicProperty
               def proc2(self, condition:bool, **kwargs) -> Dict:
                   if condition:
                       return Dict(value=True)
                   else:
                       return Dict(value=False)
                def another _function(self):
                    pipline = proc1 >> self.proc2

    Parameters
    ----------
    func : Callable[..., Dict]
        A method that defined in a class that contains the logic of creating
        the process. The Callable method must have '**kwargs' in its arguments
        (including the default 'self' argument) and returns a Dict as it payloads.

    Returns
    -------
    Callable[..., ProcessLogic]
        The decorated process. By using it like a property,
        it returns a process that can be joined or forked to others.
    """
    p_logic = ProcessLogicProperty(func)

    def logic(caller) -> ProcessLogicProperty:
        p_logic.caller_class = caller
        return p_logic
    # Turns the return to a property with a getter method
    logic_property = property(fget=logic)
    return logic_property


def processFactory(cache: bool,
                   cache_size: int = 256):
    """A factory decorator that turns a function to a process.

       The function must return a process or ImageProcessingPipeline.

    Parameters
    ----------
    cache : bool
        Cache the created pipeline based on the arguments that pass to
        the factory function.
    cache_size : int, optional
        The size of the cache, by default 256
    """
    def decorator(func):
        p_factory = ProcessFactory(func)

        if cache:
            @functools.lru_cache(cache_size)
            def cached_factory(*args, **kwargs) -> AbstractProcess:
                """Parametrisation arguments are passed here."""
                return p_factory.create(*args, **kwargs)
            return cached_factory
        else:
            def factory(*args, **kwargs) -> AbstractProcess:
                """Parametrisation arguments are passed here."""
                return p_factory.create(*args, **kwargs)
            return factory
    return decorator
