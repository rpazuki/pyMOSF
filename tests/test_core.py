import pytest

from pyMOSF.config import Dict, GUIFramework
from pyMOSF.core import (
    AbstractApp,
    AbstractLayout,
    AsyncService,
    Event,
    EventDispatcher,
    EventType,
    ServiceArgumentError,
    ServiceRegistry,
    SyncService,
)

ServiceRegistry._framework = GUIFramework.TOGA


class SingletonSyncService(SyncService):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonSyncService, cls).__new__(cls)
            # Put any initialization here.
            cls._instance.called = False
            cls._instance.exited = False
        return cls._instance

    def handle_event(self, widget, app, service_callback=None, *args, **kwargs):
        self.called = True
        if service_callback:
            service_callback(Dict(**kwargs))

    def on_exit(self):
        self.exited = True


class SingletonAsyncService(AsyncService):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonAsyncService, cls).__new__(cls)
            # Put any initialization here.
            cls._instance.called = False
            cls._instance.exited = False
        return cls._instance

    async def handle_event(self, widget, app, service_callback=None, *args, **kwargs):
        self.called = True

    def on_exit(self):
        self.exited = True


class UIElement:
    def __init__(self):
        self.id = "test"
        self.children = []

    def on_press(self):
        pass


class ConfigurableLayout(AbstractLayout):
    def __init__(self, app: AbstractApp) -> None:
        super().__init__(app)
        self.children = []
        self.common_config_called = False
        self.linux_config_called = False

    def build_layout(self, app):
        element = UIElement()
        self.children.append(element)
        return self

    def on_common_config(self):
        self.common_config_called = True
        #
        service = SingletonSyncService()
        event = Event(id="test", eventType=EventType.ON_PRESS,
                      service=service)
        registry = ServiceRegistry()
        registry.bind_event(event)

    def on_linux_config(self):
        self.linux_config_called = True


class ServicableApp(AbstractApp):
    def __init__(self):
        # Set the layout here
        super().__init__(ConfigurableLayout(self))


class FarmeworkApp(AbstractApp):
    def __init__(self):
        # Set the layout here
        super().__init__(ConfigurableLayout(self))
        self.common_config_called = False
        self.linux_config_called = False

    def framework_startup(self):
        """Assumed this function is called by framework"""
        self._set_config()
        self.on_load()

    def on_common_config(self):
        self.common_config_called = True

    def on_linux_config(self):
        self.linux_config_called = True


class LayoutWithCallback(AbstractLayout):
    def __init__(self, app: AbstractApp) -> None:
        super().__init__(app)
        self.children = []
        self.element1 = None
        self.element2 = None
        self.element3 = None
        self.element1_callback_called = False
        self.element2_callback_called = False
        self.element3_callback_called = False
        self.element3_callback_has_results = False
        self.counter = 0
        self.recived_counter = 0

    def build_layout(self, app):
        self.element1 = UIElement()
        self.element1.id = "element1"
        self.children.append(self.element1)
        self.element2 = UIElement()
        self.element2.id = "element2"
        self.children.append(self.element2)
        self.element3 = UIElement()
        self.element3.id = "element3"
        self.children.append(self.element3)
        self.element4 = UIElement()
        self.element4.id = "element4"
        self.children.append(self.element4)
        return self

    def element1_callback(self, results):
        self.element1_callback_called = True

    def element3_callback(self, results):
        self.element3_callback_called = True
        if results.has_results:
            self.element3_callback_has_results = True

    def lazy_value_loading(self):
        self.counter += 1
        return self.counter

    def element4_callback(self, results):
        if results.counter:
            self.recived_counter = results.counter

    def on_common_config(self):
        def local_callback(results):
            self.element2_callback_called = True
        #
        registry = ServiceRegistry()
        service = SingletonSyncService()
        # Bind event for element1
        event = Event(id="element1", eventType=EventType.ON_PRESS,
                      service=service,
                      service_callback=self.element1_callback)
        registry.bind_event(event)
        # Bind event for element2
        event = Event(id="element2", eventType=EventType.ON_PRESS,
                      service=service,
                      service_callback=local_callback)
        registry.bind_event(event)
        # Bind event for element3
        event = Event(id="element3", eventType=EventType.ON_PRESS,
                      service=service,
                      service_callback=self.element3_callback,
                      extra_kwargs={"has_results": True}
                      )
        registry.bind_event(event)
        # Bind event for element4
        event = Event(id="element4", eventType=EventType.ON_PRESS,
                      service=service,
                      service_callback=self.element4_callback,
                      extra_kwargs={
                          "counter": self.lazy_value_loading}
                      )
        registry.bind_event(event)


class LayoutWithCallApp(AbstractApp):
    def __init__(self):
        # Set the layout here
        super().__init__(LayoutWithCallback(self))


@pytest.fixture
def dispatcher():
    return EventDispatcher()


def test_service_registry_register():
    servicable_app = ServicableApp()
    servicable_app.on_load()  # Bind event dispatcher will happen here
    element = servicable_app.layout.children[0]  # type: ignore
    assert callable(element.on_press)
    element.on_press()
    service = SingletonSyncService()
    assert service.called


def test_service_registry_callbacks():
    #
    layout_callback_app = LayoutWithCallApp()
    layout_callback_app.on_load()  # Bind event dispatcher will happen here
    #
    element = layout_callback_app.layout.element1  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.element1_callback_called  # type: ignore
    #
    element = layout_callback_app.layout.element2  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.element2_callback_called  # type: ignore
    #
    element = layout_callback_app.layout.element3  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.element3_callback_called  # type: ignore
    assert layout_callback_app.layout.element3_callback_has_results  # type: ignore
    #
    element = layout_callback_app.layout.element4  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.recived_counter == 1  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.recived_counter == 2  # type: ignore
    element.on_press()
    assert layout_callback_app.layout.recived_counter == 3  # type: ignore


def test_event_dispatcher_dispatch(dispatcher):
    called = False

    def handler(widget, app, callback, **kwargs):
        nonlocal called
        called = True
    dispatcher.register("event1", handler)
    dispatcher.dispatch("event1", None, None, None, None)  # type: ignore
    assert called


def test_event_dispatcher_callback(dispatcher):
    called = False

    def callback(widget, app, **kwargs):
        nonlocal called
        called = True

    def handler(widget, app, callback, **kwargs):
        callback(widget, app)
    dispatcher.register("event1", handler)
    dispatcher.dispatch("event1", None, None, callback, None)  # type: ignore
    assert called


def test_service_registry_on_exit():
    service = SingletonSyncService()
    event = Event(id="exit_test", eventType=EventType.ON_PRESS,
                  service=service)
    registry = ServiceRegistry()
    registry.bind_event(event)
    registry.on_exit(None)
    assert service.exited


# @pytest.mark.asyncio
# async def test_event_dispatcher_dispatch_async(dispatcher):
#     called = False

#     async def async_handler(widget, app, **kwargs):
#         nonlocal called
#         called = True
#     dispatcher.register_async("async_event", async_handler)
#     await dispatcher.dispatch_async("async_event", None, None, None, None)
#     assert called


def test_service_argument_error():
    with pytest.raises(ServiceArgumentError) as excinfo:
        raise ServiceArgumentError("Test message")
    assert str(excinfo.value) == "Test message"


def test_configurable():
    servicable_app = ServicableApp()
    servicable_app.on_load()  # Bind event dispatcher will happen here
    assert servicable_app.layout.common_config_called   # type: ignore
    assert servicable_app.layout.linux_config_called   # type: ignore


def test_app_configurable():
    framework_app = FarmeworkApp()
    framework_app.framework_startup()  # It is called by framework
    assert framework_app.common_config_called   # type: ignore
    assert framework_app.linux_config_called   # type: ignore
    # Layout should be configured too
    assert framework_app.layout.common_config_called   # type: ignore
    assert framework_app.layout.linux_config_called   # type: ignore
