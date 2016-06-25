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

from ...teams import PRISONERS_TEAM

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


class WeaponInstant(BaseItemInstance):
    auto_activation = True
    team_restriction = (PRISONERS_TEAM, )

    def activate(self, player, amount):
        player.give_named_item(self['entity_to_give'], 0)
        return super().activate(player, amount)

register_item_instance_class('weapon_instant', WeaponInstant)
