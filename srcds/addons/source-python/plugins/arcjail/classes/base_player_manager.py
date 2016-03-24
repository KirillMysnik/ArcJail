from players.helpers import userid_from_index

from .callback import CallbackDecorator


class PlayerCallbackDecorator(CallbackDecorator):
    def __init__(self, callback, player_manager):
        self.player_manager = player_manager

        super().__init__(callback)


class OnPlayerRegistered(PlayerCallbackDecorator):
    def register(self):
        self.player_manager.register_player_registered_callback(self)

    def unregister(self):
        self.player_manager.unregister_player_registered_callback(self)


class OnPlayerUnregistered(PlayerCallbackDecorator):
    def register(self):
        self.player_manager.register_player_unregistered_callback(self)

    def unregister(self):
        self.player_manager.unregister_player_unregistered_callback(self)


class BasePlayerManager(dict):
    def __init__(self, base_class):
        super().__init__()

        self._base_class = base_class
        self._callbacks_on_player_registered = []
        self._callbacks_on_player_unregistered = []

    def create(self, player):
        self[player.userid] = self._base_class(player)
        for callback in self._callbacks_on_player_registered:
            callback(self[player.userid])

        return self[player.userid]

    def delete(self, player):
        for callback in self._callbacks_on_player_unregistered:
            callback(self[player.userid])

        return self.pop(player.userid)

    def get_by_index(self, index):
        return self.get(userid_from_index(index))

    def register_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.append(callback)

    def unregister_player_registered_callback(self, callback):
        self._callbacks_on_player_registered.remove(callback)

    def register_player_unregistered_callback(self, callback):
        self._callbacks_on_player_unregistered.append(callback)

    def unregister_player_unregistered_callback(self, callback):
        self._callbacks_on_player_unregistered.remove(callback)

    def on_player_registered(self, callback):
        return OnPlayerRegistered(callback, self)

    def on_player_unregistered(self, callback):
        return OnPlayerUnregistered(callback, self)
