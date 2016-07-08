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

"""
Removes the need to use game_player_equip entity on the jail maps.
Replaces game_player_equip stripping functionality on CS:GO as the entity
does not work for that game.
"""

from entities.entity import Entity
from listeners import OnEntitySpawned

from ..arcjail import InternalEvent

from ..common import give_named_item

from .equipment_switcher import saved_player_manager


@OnEntitySpawned
def listener_on_entity_spawned(index, base_entity):
    if base_entity.classname != "game_player_equip":
        return

    Entity(index).remove()


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    saved_player = saved_player_manager[player.index]

    saved_player.strip()

    give_named_item(player, "weapon_knife")
