"""The core module.

   Notes:
   ------

    1- Service handler's arguments
        Service's 'handle_event' arguments can be provided by
        the caller on binding time. To do that, you must set the
        Event's extra_kwargs : mapping[str, ServiceCallable | Any ].

        Mapping's key is the name of the argument. Mapping's value can
        be passed as Any, or can be a ServiceCallable type to be loaded
        lazily: 'type  ServiceCallable = Callable[[None | object], Any]'

        In other words, in the former case, the same value will send
        to to service every time that the 'handle_event' is called,
        and in the latter case, the Callable updates the value of
        the argument each time the 'handle_event' is called.
        The ServiceCallable signutare MUST have zero argument, or for class
        function, the 'self' argument.

        It can raise 'ServiceArgumentError'.

    2- Service handler's arguments as callback
        When the service argument is a callback, which will be called
        later by the 'handle_event', it MUST be decorated by @service_callback.
        It becomes clear, if we  consider that the arguments can be lazily
        loaded, and so, it can be a Callable. As a result, on calling the
        service's 'handle_event', it must be differentiated between Callable
        as lazy load or callback.

        It can raise 'ServiceArgumentError'.

    3- Configurable
       Both AbstractApp , AbstractLayout and TogaComponent
       are 'Configurable'. So, they can impliment
       os dependent configuration.

       AbstractApp calls 'Configurable' once in its
       lifcycle:  on_begin().

       AbstractLayout calls 'Configurable' once on its
       first load: on_load.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from inspect import signature
from typing import Any, Callable, Mapping

from pyMOSF.config import Configurable, GUIFramework, Settings
from pyMOSF.core.__loggers__ import file_out_log, std_out_log

log = logging.getLogger(__name__)


class ServiceArgumentError(Exception):
    def __init__(self, message: str, cause=None) -> None:
        self.message = message
        self.__cause__ = cause
        super().__init__(self.message)


class EventType(Enum):
    ON_PRESS = 0
    ON_RELEASE = 1
    ON_CHANGE = 2
    ON_TOUCH_DOWN = 3
    ON_TOUCH_MOVE = 4
    ON_TOUCH_UP = 5
    BIND = 100

    @staticmethod
    def get_all_eventTypes():
        return vars(EventType)['_member_names_']


class Updateable:
    def on_update(self, **kwargs):
        """Update the component with new data."""
        pass


class Service(ABC):
    """An abstract class for handeling UI event callbacks
    """

    @abstractmethod
    def handle_event(self,
                     widget: Any,
                     app,
                     service_callback: Callable | None = None,
                     *args,
                     **kwargs) -> None:
        """An abstract class for handeling UI sync event callbacks
        """
        pass

    def on_exit(self) -> None:
        """The event handler that will be invoked when the app is about to exit.
        """
        pass


# Accept zero or one argument
# type  ServiceCallback = Callable[[object | Dict], None]


class Event:
    def __init__(self,
                 id: str,
                 eventType: EventType,
                 service: Service,
                 property_name: str = "",
                 extra_kwargs: Mapping[str, Any] = {},
                 service_callback=None
                 ) -> None:
        self.id = id
        self.eventType = eventType
        self.service = service
        self.property_name = property_name
        self.extra_kwargs = extra_kwargs
        self.service_callback = service_callback

    def element_event(self, element):
        return getattr(element, self.eventType.name.lower())


class AbstractLayout(ABC, Configurable,  Updateable):
    def __init__(self, app: AbstractApp) -> None:
        super(AbstractLayout, self).__init__()
        self._app = app

    @property
    def _name(self):
        return type(self).__qualname__

    @abstractmethod
    def build_layout(self, app) -> Any:
        pass

    @property
    def ml_app(self) -> AbstractApp:
        if self._app is None:
            raise ValueError("app has not been initialized.")
        return self._app

    def on_load(self):
        pass

    def on_end(self):
        pass


class AbstractApp(ABC, Configurable):
    def __init__(self,
                 layout: AbstractLayout,
                 settings: Settings | None = None,
                 **kwargs) -> None:
        super(AbstractApp, self).__init__(**kwargs)
        self._settings = settings
        self.layout = layout
        self.reset_event_dispatchers_table()

    def reset_event_dispatchers_table(self):
        self._event_dispatchers_table = {}
        for t in EventType.get_all_eventTypes():
            self._event_dispatchers_table[t] = {}

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = Settings.load(self.data_path)
        return self._settings

    @property
    def event_dispatchers_table(self):
        """Stores different event_dispatchers per EventType.

        event_dispatchers_table is dictionary or dictionaries that
        EventType is its key and event_dispatchers are dictionaries
        of (id : UI element).
        """
        return self._event_dispatchers_table

    @property
    def path(self):
        raise NotImplementedError()

    @property
    def data_path(self):
        raise NotImplementedError()

    def on_begin(self):
        """The event handler that will be invoked when the app is about to start.

        It calls only once, in contrast to 'on_load_window', therefore, app settings
        is called once during the life-cycle of an app.

        It calls the build_layout of Layout instance, stores all UI elements with
        id and suport of one or more events in event_dispatchers_table, and registers
        them in ServiceRegistry.
        """
        self._set_config()
        self.on_load()

    def on_load(self):
        """The event handler that will be invoked when the app is reset the layout.

        It can be called any time the layout or main window chances, in contrast to
        'on_begin'.

        It calls the build_layout of Layout instance, stores all UI elements with
        id and suport of one or more events in event_dispatchers_table, and registers
        them in ServiceRegistry.
        """
        root = self.layout.build_layout(self)

        # self.reset_event_dispatchers_table()
        self.__enumerate_elements(root)
        # Initial Event bindings definitions happens here
        registry = ServiceRegistry()
        #
        previous_events = [id for id in registry.events]
        self.layout._set_config()
        # Event bindings to dispatcher happens here

        for id, event in registry.events.items():
            event_dispatcher = self.event_dispatchers_table[event.eventType.name]
            if id in previous_events:
                continue
            if id not in event_dispatcher:
                raise ValueError(
                    f" Widget id:'{id}' for the {event.eventType.name} handler "
                    f"has no corresponding UI. Check the bindings map.")
            element = event_dispatcher[id]
            registry.register_service(event,
                                      element,
                                      app=self)
        #
        self.layout.on_load()

    def on_end(self) -> bool:
        """The event handler that will be invoked when the app is about to exit.

        It calls the on_exit of all services in the ServiceRegistry.
        """
        registry = ServiceRegistry()
        registry.on_exit(self)
        self.layout.on_end()
        self.settings.on_end()
        return True

    def __enumerate_elements(self, root):
        """Recursivly searches and records all elements.
        """

        def creat_method_checker(name):
            """Create a function that checks availibility of a method
            """
            def checker(obj):
                """A combinations of attribute name and callable"""
                method = getattr(obj, name, None)
                return method is not None and callable(method)

            return checker

        event_checkers = [(t, creat_method_checker(t.lower()))
                          for t in EventType.get_all_eventTypes()]

        def recursive(parent):
            """Recusricly check all UI's tree elements.

               If the element has both an id and a corresponding
               event, it will be stored in event_dispatchers.
            """
            for child in parent.children:
                # event_checkers contains both the eventType and corresponding
                # method (has_event) that check the availibity of the event.
                # e.g. for EventType.ON_PRESS, has_event looks for UI element's
                # on_press event support.
                for eventType, has_event in event_checkers:
                    if has_event(child) and hasattr(child, "id") is True:
                        # event_dispatchers_table is dictionary or dictionaries
                        event_dispatchers = self.event_dispatchers_table[eventType]
                        event_dispatchers[child.id] = child
                recursive(child)

        recursive(root)

    def update(self, **kwargs):
        """Update the component with new data."""
        self.layout.on_update(**kwargs)

    def set_logger(self,
                   std_out: bool = True,
                   file_out: bool = False,
                   file_name: str = "log.txt",
                   log_level: int = logging.ERROR):
        if std_out:
            std_out_log(log_level=logging.getLevelName(log_level))
        if file_out:
            file_out_log(path=self.data_path / file_name,
                         log_level=logging.getLevelName(log_level))


class ServiceRegistry(object):
    """A singleton object that store the required (id: ServiceStrategy).
    """
    _instance = None
    _framework: GUIFramework = GUIFramework.UKNOWN

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
            # Put any initialization here.
            cls._instance._dispatcher = EventDispatcher()
        return cls._instance

    __events = {}
    _dispatcher: EventDispatcher

    @property
    def dispatcher(self):
        return self._dispatcher

    @property
    def events(self):
        return self.__events

    def bind(self,
             *,
             id: str,
             eventType: EventType,
             service,
             property_name: str = "",  # kivy only, to be used by its bind
             extra_kwargs: Mapping[str, Any] = {},
             service_callback=None) -> None:
        self.events[id] = Event(id, eventType, service,
                                property_name, extra_kwargs,
                                service_callback)

    def bind_event(self, event: Event) -> None:
        self.events[event.id] = event

    def get_event_info(self, id) -> Event:
        return self.events.get(id, None)  # type: ignore

    def register_service(self, event: Event, element: Any, app: AbstractApp):
        """Register a ServiceStrategy for the given event, UI element and app.

           A callback will be attached to the event handler of the UI element.
           If the UI element has also a handler, it will be included in the call
           qeue.


        Parameters
        ----------
        event : Event
            The event object that includes id and ServiceStrategy.
        element : Any
            UI element that can handel th event.
        app : AbstractApp
            The app object.
        """
        if event.extra_kwargs is not {} and not isinstance(event.extra_kwargs, Mapping):
            raise ValueError(
                f" Widget id:'{event.id}' ({type(element).__name__}) "
                f"asked for {event.eventType.name} handler, but did not provide "
                f"the binding arguments (Mapping). Check the bindings map.")
        #

        def attach(callback):
            # setattr(element, registeredEventType.name.lower(), callback)
            match ServiceRegistry._framework:
                case GUIFramework.TOGA:
                    # from toga.handlers import wrapped_handler  # type: ignore

                    handler = callback  # wrapped_handler(element, callback)
                    # handler = wrapped_handler(element, callback)
                    # e.g. element.on_press = handler
                    setattr(element, event.eventType.name.lower(), handler)
                case GUIFramework.KIVY:
                    # Only BIND
                    if event.eventType == EventType.BIND:
                        if event.property_name == "":
                            raise ValueError(
                                f" Widget id:'{event.id}' ({type(element).__name__}) "
                                f"asked for {event.eventType.name} handler, but did not "
                                f"provide the 'property_name'. Check the bindings map.")
                        if not isinstance(event.property_name, str):
                            raise ValueError(
                                f" Widget id:'{event.id}' ({type(element).__name__}) "
                                f"asked for {event.eventType.name} handler, but did not provide "
                                f"the binding argument name (str). Check the bindings map.")
                        # e.g. switch.bind(active=callback)
                        kwrgs = {event.property_name: callback}
                        element.bind(**kwrgs)
                    else:
                        # e.g. button.bind(on_press=callback)
                        kwrgs = {event.eventType.name.lower(): callback}
                        element.bind(**kwrgs)
                case _:
                    raise ValueError(
                        f" Unknown UI Framework: {ServiceRegistry._framework}")
        #
        element_event = event.element_event(element)
        if hasattr(element_event, "_raw"):
            handler = element_event._raw  # This is toga's wrapped_handler attribute
        else:
            handler = element_event  # kivy

        #
        match event.service:
            case SyncService():
                if handler is not None:
                    self.dispatcher.register_framework(event.id, handler)
                self.dispatcher.register(event.id, event.service.handle_event)
                handler_2 = self.dispatcher.service_callback(event.id,
                                                             element,
                                                             app,
                                                             event.service_callback,
                                                             event.extra_kwargs)
                attach(handler_2)
            case AsyncService():
                if handler is not None:
                    self.dispatcher.register_async_framework(event.id, handler)
                self.dispatcher.register_async(
                    event.id, event.service.handle_event)
                handler_2 = self.dispatcher.service_async_callback(event.id,
                                                                   element,
                                                                   app,
                                                                   event.service_callback,
                                                                   event.extra_kwargs)
                attach(handler_2)
            case _:
                log.warning(
                    f" Widget id:'{event.id}' ({type(element).__name__}) "
                    f"did not bind to any {event.eventType.name} handler. Check the bindings map.")

    def on_exit(self, app):
        """The event handler that will be invoked when the app is about to exit.

        It calls the on_exit of all registred services.
        """
        for eventInfo in self.events.values():
            eventInfo.service.on_exit()

        # for id, event in self.events.items():
        #     event_dispatcher = app.event_dispatchers_table[event.eventType.name]
        #     element = event_dispatcher[id]
        #     print(element)

    def fire_event(self, id, app):
        event = self.get_event_info(id)
        event_dispatcher = app.event_dispatchers_table[event.eventType.name]
        element = event_dispatcher[id]
        callback = self.dispatcher.service_callback(event.id,
                                                    element,
                                                    app,
                                                    event.service_callback,
                                                    event.extra_kwargs)
        callback()

    async def fire_async_event(self, id, app):
        event = self.get_event_info(id)
        event_dispatcher = app.event_dispatchers_table[event.eventType.name]
        element = event_dispatcher[id]
        callback = self.dispatcher.service_async_callback(event.id,
                                                          element,
                                                          app,
                                                          event.service_callback,
                                                          event.extra_kwargs)
        await callback()


class EventDispatcher:
    """Event dispatcher that binds the UI elements call back to EventStrategy instances.

    This is a lightweight event dispatcher that can support both sync and async calls.
    """

    def __init__(self):
        self.reset_listeners()

    def reset_listeners(self):
        self.listeners = {}
        self.listeners_framework = {}
        self.async_listeners = {}
        self.async_listeners_framework = {}

    #
    def register(self, event_name: str, handler):
        """Register a synchronous callback for an event.

        Parameters
        ----------
        event_name : str
            The name of the event to register.
        handler : function
            The function to call when the event is triggered.
        """
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(handler)

    def register_framework(self, event_name: str, handler):
        """Register a synchronous callback for an event that has already binded in the framework.

        Parameters
        ----------
        event_name : str
            The name of the event to register.
        handler : function
            The function to call when the event is triggered.
        """
        if event_name not in self.listeners_framework:
            self.listeners_framework[event_name] = []
        self.listeners_framework[event_name].append((handler,
                                                     signature(handler)))

    def register_async(self, event_name: str, async_handler):
        """Register an asynchronous callback for an event.

        Parameters
        ----------
        event_name : str
            The name of the event to register.
        async_handler : function
            The async function to call when the event is triggered.
        """

        if event_name not in self.async_listeners:
            self.async_listeners[event_name] = []
        self.async_listeners[event_name].append(async_handler)

    def register_async_framework(self, event_name: str, async_handler):
        """Register an asynchronous callback for an event that has already binded in the framework.

        Parameters
        ----------
        event_name : str
            The name of the event to register.
        async_handler : function
            The async function to call when the event is triggered.
        """

        if event_name not in self.async_listeners_framework:
            self.async_listeners_framework[event_name] = []
        self.async_listeners_framework[event_name].append((async_handler,
                                                           signature(async_handler)))
    #

    def dispatch(self,
                 event_name: str,
                 widget: Any,
                 app: AbstractApp,
                 call_back,
                 extrakwargs: Mapping,
                 *args,
                 **kwargs):
        """Dispatch a synchronous event to all registered callbacks.

        Parameters
        ----------
        event_name : str
            The name of the event to dispatch.
        widget : Any
            UI element.
        app : AbstractApp
            The AbstractApp subclass that registred the elements.
        call_back: ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        extrakwargs : Mapping
            Extra key-value paires can be provided to pass to the handler.
            If the value is a callable, it is called each time the event happens.
            This is useful when the arguments need to be updated, e.g., from the
            value in the UI.
        """
        if ServiceRegistry._framework == GUIFramework.TOGA:
            for binded_method, sig in self.listeners_framework.get(event_name, []):
                binded_method(*args, **kwargs)

        for binded_method in self.listeners.get(event_name, []):
            if extrakwargs is None:
                binded_method(widget, app, call_back, *args, **kwargs)
            else:
                kwargs2 = {}
                for k, v in extrakwargs.items():
                    if callable(v):
                        parameters = signature(v).parameters
                        if len(parameters) > 1:
                            raise ServiceArgumentError(
                                message=f"In setting the parameter '{k}', the signuture of "
                                f"function '{v.__name__}' for service handler "
                                f"of the {event_name=} must have zero or self argument, it needs "
                                f"{len(parameters):d} = {list(parameters.keys())}. "
                                "(You might need to decorate it by @component_method."
                            )
                        else:
                            try:
                                kwargs2[k] = v()
                            except TypeError as e:
                                raise ServiceArgumentError(
                                    message="Service lazy argument caused an error. "
                                    "check the function accept zero or at most one "
                                    "argument, 'self'.",
                                    cause=e
                                )

                    else:
                        kwargs2[k] = v

                binded_method(widget, app, call_back, **kwargs2)

    async def dispatch_async(self,
                             event_name: str,
                             widget: Any,
                             app: AbstractApp,
                             call_back,
                             extrakwargs: Mapping,
                             *args,
                             **kwargs):
        """Dispatch a asynchronous event to all registered callbacks.

        Parameters
        ----------
        event_name : str
            The name of the event to dispatch.
        widget : Any
            UI element.
        app : AbstractApp
            The AbstractApp subclass that registred the elements.
        call_back: ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        extrakwargs : Mapping
            Extra key-value paires can be provided to pass to the handler.
            If the value is a callable, it is called each time the event happens.
            This is useful when the arguments need to be updated, e.g., from the
            value in the UI.
        """
        if ServiceRegistry._framework == GUIFramework.TOGA:
            for binded_method, sig in self.async_listeners_framework.get(event_name, []):
                binded_method(*args, **kwargs)
        for binded_method in self.async_listeners.get(event_name, []):
            if extrakwargs is None:
                await binded_method(widget, app, call_back, *args, **kwargs)
            else:
                kwargs2 = {}
                for k, v in extrakwargs.items():
                    if callable(v):
                        parameters = signature(v).parameters
                        if len(parameters) > 1:
                            raise ValueError(
                                f"In setting the parameter '{k}', the signuture of function "
                                f"'{v.__name__}' for service handler "
                                f"of the {event_name=} must have zero or self argument, it needs "
                                f"{len(parameters):d} = {list(parameters.keys())}. "
                                "(You might need to decorate it by @component_method "
                                "or @service_callback)."
                            )
                        else:
                            try:
                                kwargs2[k] = v()
                            except TypeError as e:
                                raise ServiceArgumentError(
                                    message="Service lazy argument caused an error. "
                                    "check the function accept zero or at most one "
                                    "argument, 'self'.",
                                    cause=e
                                )

                    else:
                        kwargs2[k] = v

                await binded_method(widget, app, call_back, **kwargs2)

    def service_callback(self,
                         id: str,
                         widget: Any,
                         app: AbstractApp,
                         call_back,
                         extrakwargs: Mapping):
        """Create a synchronous widget callback for a ServiceStrategy instance.

        Parameters
        ----------
        id : str
            The ID of the widget.
        widget : Any
            The UI element that registers the and will call the callback.
        app : AbstractApp
            The application instance.
        call_back: ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        extrakwargs : Mapping
            Extra argument that maybe provided on binding table.

        Returns
        -------
        function
            A decorated callback function.
        """
        def callback(*args, **kwargs):
            self.dispatch(id, widget, app, call_back,
                          extrakwargs, *args, **kwargs)

        return callback

    def service_async_callback(self,
                               id: str,
                               widget: Any,
                               app: AbstractApp,
                               call_back,
                               extrakwargs: Mapping):
        """Create an asynchronous widget callback for a ServiceStrategy instance.

        Parameters
        ----------
        id : str
            The ID of the widget.
        widget : Any
            The UI element that registers the and will call the callback.
        app : AbstractApp
            The application instance.
        call_back: ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        extrakwargs : Mapping
            Extra argument that maybe provided on binding table.

        Returns
        -------
        function
            A decorated async callback function.
        """
        async def async_callback(*args, **kwargs):
            await self.dispatch_async(id, widget, app, call_back, extrakwargs, *args, **kwargs)

        return async_callback


class SyncService(Service):
    """An abstract class for handeling UI sync event callbacks
    """

    @abstractmethod
    def handle_event(self,
                     widget: Any,
                     app: AbstractApp,
                     service_callback,
                     *args,
                     **kwargs) -> None:
        """Sync event handler

        Parameters
        ----------
        widget : Any
            The widget that called the handler.
        app : AbstractApp
            The parent application of the widget.
        service_callback : ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        """
        pass


class AsyncService(Service):
    """An abstract class for handeling UI async event callbacks
    """

    @abstractmethod
    async def handle_event(self,
                           widget: Any,
                           app: AbstractApp,
                           service_callback,
                           *args,
                           **kwargs) -> None:
        """Async event handler.

        Parameters
        ----------
        widget : Any
            The widget that called the handler.
        app : AbstractApp
            The parent application of the widget.
        service_callback : ServiceCallback | None
            The callback function that will be called after the event to
            send the possible result.
        """
        pass
