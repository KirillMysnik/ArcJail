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

from controlled_cvars import InvalidValue

from ..arcjail import InternalEvent

from . import build_module_config


config_manager = build_module_config('max_health')


def _default_value_handler(cvar):
    try:
        hp = int(cvar.get_string())
    except ValueError:
        raise InvalidValue

    if hp <= 0:
        raise InvalidValue

    return hp

config_manager.controlled_cvar(
    _default_value_handler,
    "default_value",
    default=100,
    description="Default maximum health for every player",
)

players = {}


def upgrade_health(player, new_amount):
    """Set player's health to max(<current amount>, new_amount)"""
    player.health = max(player.health, new_amount)


def restore_health(player):
    """Restore player's health to its maximum"""
    player.health = max(player.health, players[player.index])


def set_max_health(player, amount):
    """Set player's health maximum"""
    players[player.index] = amount


def upgrade_max_health(player, new_amount):
    """Set player's maximum health to max(<current max health amount>, amount)"""
    players[player.index] = max(players[player.index], new_amount)


def get_max_health(player):
    """Return player's health maximum"""
    return players[player.index]


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    set_max_health(player, config_manager['default_value'])
    restore_health(player)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    set_max_health(event_var['main_player'], config_manager['default_value'])


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    del players[event_var['main_player'].index]
