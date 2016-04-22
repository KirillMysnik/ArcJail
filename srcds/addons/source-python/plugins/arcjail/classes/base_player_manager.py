# This file is part of ArcJail.
#
# ArcJail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ArcJail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ArcJail.  If not, see <http://www.gnu.org/licenses/>.

from players.helpers import index_from_userid

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
        self[player.index] = self._base_class(player)
        for callback in self._callbacks_on_player_registered:
            callback(self[player.index])

        return self[player.index]

    def delete(self, player):
        for callback in self._callbacks_on_player_unregistered:
            callback(self[player.index])

        return self.pop(player.index)

    def get_by_userid(self, userid):
        return self.get(index_from_userid(userid))

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
