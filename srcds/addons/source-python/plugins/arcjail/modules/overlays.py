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

from events import Event
from listeners.tick import Delay

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager


class OverlayPlayer:
    def __init__(self, player):
        self.player = player
        self._overlays = []
        self._delays = []

    def show(self, path, seconds=-1):
        self._overlays.insert(0, path)
        if seconds > 0:
            self._delays.append(Delay(seconds, self._remove, path))

        self._update()

    def clear(self):
        for delay in self._delays:
            if delay.running:
                delay.cancel()

        self._delays.clear()

        self._overlays.clear()
        self._update()

    def _remove(self, path):
        self._overlays.remove(path)
        self._update()

    def _update(self):
        if self._overlays:
            self.player.client_command(
                'r_screenoverlay {}'.format(self._overlays[0]))
        else:
            self.player.client_command('r_screenoverlay off')

overlay_player_manager = BasePlayerManager(OverlayPlayer)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    overlay_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    overlay_player_manager.delete(player)


@Event('round_start')
def on_round_start(game_event):
    for overlay_player in overlay_player_manager.values():
        overlay_player.clear()


def show_overlay(player, path, seconds=-1):
    overlay_player = overlay_player_manager[player.index]
    overlay_player.show(path, seconds)
