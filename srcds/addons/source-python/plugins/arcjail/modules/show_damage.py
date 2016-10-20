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
from messages import TextMsg

from controlled_cvars.handlers import sound_nullable_handler, string_handler

from ..internal_events import InternalEvent
from ..classes.base_player_manager import BasePlayerManager
from ..resource.strings import build_module_strings

from . import build_module_config
from .overlays import show_overlay


TEXT_VISIBLE_TIMEOUT = 2
MARKER_VISIBLE_TIMEOUT = 0.2
EMPTY_CENTER_MESSAGE = TextMsg("")


strings_module = build_module_strings('show_damage')
config_manager = build_module_config('show_damage')

config_manager.controlled_cvar(
    sound_nullable_handler,
    "hit_sound",
    default="arcjail/hitsound.wav",
    description="Path to a hit sound, leave empty to disable",
)
config_manager.controlled_cvar(
    string_handler,
    "hit_marker_material",
    default="overlays/arcjail/hitmarker",
    description="Path to a hit marker material (VMT-file) without VMT "
                "extension, leave empty to disable",
)


class ShowDamagePlayer:
    def __init__(self, player):
        self.player = player
        self._current_damage = 0
        self._reset_text_delay = None

    def _reset_text(self):
        self._current_damage = 0
        EMPTY_CENTER_MESSAGE.send(self.player.index)

    def show_damage(self, amount):
        self._current_damage += amount

        # Display damage amount
        TextMsg(strings_module['health'].tokenize(
            amount=self._current_damage)).send(self.player.index)

        # Play hit sound
        if config_manager['hit_sound'] is not None:
            config_manager['hit_sound'].play(self.player.index)

        # Show hit marker
        if config_manager['hit_marker_material'] != "":
            show_overlay(
                self.player,
                config_manager['hit_marker_material'],
                MARKER_VISIBLE_TIMEOUT
            )

        # Cancel delays if any
        if (self._reset_text_delay is not None and
                self._reset_text_delay.running):

            self._reset_text_delay.cancel()

        # Relaunch delays
        self._reset_text_delay = Delay(TEXT_VISIBLE_TIMEOUT, self._reset_text)


show_damage_player_manager = BasePlayerManager(ShowDamagePlayer)


@InternalEvent('player_created')
def on_player_created(player):
    show_damage_player_manager.create(player)


@InternalEvent('player_deleted')
def on_player_deleted(player):
    show_damage_player_manager.delete(player)


def show_damage(player, amount):
    sd_player = show_damage_player_manager[player.index]
    sd_player.show_damage(int(amount))
