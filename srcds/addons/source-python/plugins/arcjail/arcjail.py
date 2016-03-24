from traceback import format_exc

from filters.players import PlayerIter
from listeners import OnClientActive, OnClientDisconnect, OnLevelInit
from paths import CFG_PATH
from players.entity import Player
from stringtables.downloads import Downloadables

from .info import info

from .classes.base_player_manager import BasePlayerManager
from .classes.callback import CallbackDecorator


DOWNLOADLIST = CFG_PATH / info.basename / "downloadlists" / "main.txt"


def load_downloadables(filepath):
    downloadables = Downloadables()

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables

downloadables_global = load_downloadables(DOWNLOADLIST)

player_manager = BasePlayerManager(lambda player: player)


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
    def __init__(self, event_name, event_manager=internal_event_manager):
        self.event_name = event_name
        self.event_manager = event_manager

    def __call__(self, handler):
        self.register(handler)

    def register(self, handler):
        self.event_manager.register_event_handler(self.event_name, handler)

    def unregister(self, handler):
        self.event_manager.register_event_handler(self.event_name, handler)

    @staticmethod
    def fire(self, event_name, event_var):
        self.event_manager.fire(event_name, event_var)


plugin_load_callbacks = []
plugin_unload_callbacks = []


class OnPluginLoad(CallbackDecorator):
    def register(self):
        plugin_load_callbacks.append(self)

    def unregister(self):
        plugin_load_callbacks.remove(self)


class OnPluginUnload(CallbackDecorator):
    def register(self):
        plugin_unload_callbacks.append(self)

    def unregister(self):
        plugin_unload_callbacks.remove(self)


def load():
    for player in PlayerIter():
        player_manager.create(player)

    for callback in plugin_load_callbacks:
        callback()


def unload():
    for callback in plugin_unload_callbacks:
        callback()

    for player in list(player_manager.values()):
        player_manager.delete(player)


@OnClientActive
def listener_on_client_active(index):
    player = Player(index)
    player_manager.create(player)


@OnClientDisconnect
def on_client_disconnect(index):
    player = Player(index)
    player_manager.delete(player)


@OnLevelInit
def listener_on_level_init(map_name):
    for player in list(player_manager.keys()):
        player_manager.delete(player)


from . import modules

from . import models
from .resource.sqlalchemy import Base, engine
Base.metadata.create_all(engine)
