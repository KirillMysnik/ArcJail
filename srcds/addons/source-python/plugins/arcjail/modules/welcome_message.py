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

from listeners.tick import Delay

from controlled_cvars.handlers import bool_handler, sound_handler

from ..arcjail import load_downloadables
from ..internal_events import InternalEvent

from . import build_module_config
from .players import player_manager


SPAWN_ANNOUNCE_DELAY = 2.0


config_manager = build_module_config('welcome_message')
config_manager.controlled_cvar(
    bool_handler,
    name="enabled",
    default=1,
    description="Enable/Disable welcome messages",
)
config_manager.controlled_cvar(
    sound_handler,
    name="sound",
    default="arcjail/welcome.mp3",
    description="Welcome sound",
)

_announced_uids = {}
_downloads = load_downloadables('welcome-sounds.res')


def announce(player):
    if config_manager['sound'] is not None:
        config_manager['sound'].play(player.index)


@InternalEvent('player_respawn')
def on_player_respawn(player):
    if player.index not in _announced_uids:
        _announced_uids[player.index] = Delay(
            SPAWN_ANNOUNCE_DELAY, announce, player)


@InternalEvent('players_loaded')
def on_players_loaded():
    for player in player_manager.values():
        _announced_uids[player.index] = None
        announce(player)


@InternalEvent('player_deleted')
def on_player_deleted(player):
    if player.index in _announced_uids:
        if (_announced_uids[player.index] is not None and
                _announced_uids[player.index].running):

            _announced_uids[player.index].cancel()

        del _announced_uids[player.index]
