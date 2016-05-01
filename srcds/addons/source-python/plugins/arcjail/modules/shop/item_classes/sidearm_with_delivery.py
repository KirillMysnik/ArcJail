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

from ....arcjail import InternalEvent

from ....resource.strings import build_module_strings

from ...teams import PRISONERS_TEAM

from ..base_classes.base_item import BaseItem

from .. import (
    get_player_item, items_json, register_item_class, take_item_from_player)


ITEM_ID = "sidearm_with_delivery"


strings_module = build_module_strings('shop/items/sidearm_with_delivery')


class SidearmWithDelivery(BaseItem):
    id = ITEM_ID
    caption = strings_module['title']
    description = strings_module['description']
    icon = "pistol-delivered.png"
    max_per_slot = 1
    team_restriction = (PRISONERS_TEAM, )
    price = items_json[ITEM_ID]['price']

register_item_class(SidearmWithDelivery)


@InternalEvent("player_respawn")
def on_player_respawn(event_var):
    player = event_var['player']

    if get_player_item(player, ITEM_ID) is not None:
        take_item_from_player(player, ITEM_ID)
        player.give_named_item(items_json[ITEM_ID]['entity_to_give'], 0)
