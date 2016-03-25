from stringtables.downloads import Downloadables

from .resource.paths import DOWNLOADLISTS_PATH


def load_downloadables(file_name):
    file_path = DOWNLOADLISTS_PATH / file_name
    downloadables = Downloadables()

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables


class InternalEventManager(dict):
    def register_event_handler(self, event_name, handler):
        if event_name not in self:
            self[event_name] = []

        if handler in self[event_name]:
            raise ValueError("Handler {} is already registered to "
                             "handle '{}'".format(handler, event_name))

        self[event_name].append(handler)

    def unregister_event_handler(self, event_name, handler):
        if event_name not in self:
            raise KeyError("No '{}' event handlers are registered".format(
                event_name))

        self[event_name].remove(handler)

        if not self[event_name]:
            del self[event_name]

    def fire(self, event_name, event_var):
        exceptions = []
        for handler in self.get(event_name, ()):
            try:
                handler(event_var)
            except Exception as e:
                exceptions.append(e)

        if exceptions:
            print("{} exceptions were raised during "
                  "handling of '{}' event".format(event_name))

            print("Raising the first one...")

            raise exceptions.pop(0)

internal_event_manager = InternalEventManager()


class InternalEvent:
    def __init__(self, event_name):
        self.event_name = event_name

    def __call__(self, handler):
        self.register(handler)

    def register(self, handler):
        internal_event_manager.register_event_handler(self.event_name, handler)

    def unregister(self, handler):
        internal_event_manager.unregister_event_handler(
            self.event_name, handler)

    @staticmethod
    def fire(event_name, **event_var):
        internal_event_manager.fire(event_name, event_var)


def load():
    InternalEvent.fire('load')


def unload():
    InternalEvent.fire('unload')


from . import modules

from . import models
from .resource.sqlalchemy import Base, engine
Base.metadata.create_all(engine)
