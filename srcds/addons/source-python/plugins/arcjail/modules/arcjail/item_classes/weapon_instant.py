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

from listeners import OnClientDisconnect

from ....resource.strings import build_module_strings

from ...teams import PRISONERS_TEAM

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


MAX_SOLD_WEAPONS_PER_PLAYER = 2


strings_module = build_module_strings('arcjail/items/weapon_instant')
sold_weapons = {}


class WeaponInstant(BaseItemInstance):
    auto_activation = True
    team_restriction = (PRISONERS_TEAM, )

    def get_purchase_denial_reason(self, player, amount):
        reason = super().get_purchase_denial_reason(player, amount)
        if reason is not None:
            return reason

        if (sold_weapons.get(player.index, 0) + amount >
                MAX_SOLD_WEAPONS_PER_PLAYER):

            return strings_module['purchase_fail too_many']

        return None

    def try_activate(self, player, amount, async=True):
        reason = super().try_activate(player, amount, async)
        if reason is not None:
            return reason

        sold_weapons[player.index] = sold_weapons.get(player.index, 0) + 1

        player.give_named_item(self['entity_to_give'], 0)
        return None

register_item_instance_class('weapon_instant', WeaponInstant)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    if index in sold_weapons:
        del sold_weapons[index]


@Event('round_start')
def on_round_start(game_event):
    sold_weapons.clear()
