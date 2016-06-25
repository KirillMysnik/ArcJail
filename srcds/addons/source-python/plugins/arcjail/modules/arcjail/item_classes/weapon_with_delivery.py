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

from ...teams import PRISONERS_TEAM

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


class WeaponWithDelivery(BaseItemInstance):
    team_restriction = (PRISONERS_TEAM, )

register_item_instance_class('weapon_with_delivery', WeaponWithDelivery)


@InternalEvent("player_respawn")
def on_player_respawn(event_var):
    from ..arcjail_user import arcjail_user_manager

    player = event_var['player']
    if player.team not in WeaponWithDelivery.team_restriction:
        return

    arcjail_user = arcjail_user_manager[player.index]

    for item in arcjail_user.iter_items_by_class_id('weapon_with_delivery'):
        arcjail_user.take_item(item, amount=1, async=True)

        # TODO: Adjust give_named_item to CS:GO
        player.give_named_item(item.class_['entity_to_give'], 0)
