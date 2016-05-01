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

from ....resource.strings import build_module_strings

from ...teams import PRISONERS_TEAM

from ..base_classes.base_item import BaseItem

from .. import items_json, register_item_class


ITEM_ID = "sidearm_instant"


strings_module = build_module_strings('shop/items/sidearm_instant')


class SidearmInstant(BaseItem):
    id = ITEM_ID
    caption = strings_module['title']
    description = strings_module['description']
    icon = "pistol.png"
    max_per_slot = 1
    auto_activation = True
    team_restriction = (PRISONERS_TEAM, )
    max_sold_per_round = 10
    price = items_json[ITEM_ID]['price']

    def activate(self):
        super().activate()

        self.player.give_named_item(items_json[ITEM_ID]['entity_to_give'], 0)


register_item_class(SidearmInstant)
