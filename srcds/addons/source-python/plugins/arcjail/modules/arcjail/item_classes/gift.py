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

from random import choice

from ....resource.strings import build_module_strings

from ...players import tell

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


strings_module = build_module_strings('arcjail/items/gift')


class Gift(BaseItemInstance):
    manual_activation = True
    use_only_when_alive = False

    def get_purchase_denial_reason(self, player, amount):
        reason = super().get_purchase_denial_reason(player, amount)
        if reason is not None:
            return reason

        return strings_module['purchase_fail impossible']

    def try_activate(self, player, amount, async=True):
        if self['gift_type'] == "credits":
            from ...credits import earn_credits
            
            earn_credits(player, self['credits_given'],
                         strings_module['credits_reason'])

        elif self['gift_type'] == "items":
            from ...arcjail.arcjail_user import arcjail_user_manager
            from . import get_item_instance

            item_json = choice(self['item_pool'])
            arcjail_user = arcjail_user_manager[player.index]
            arcjail_user.give_item(
                item_json['class_id'], item_json['instance_id'],
                amount=item_json['amount'], async=async)

            item_instance = get_item_instance(
                item_json['class_id'], item_json['instance_id'])

            tell(player, strings_module['item_received'],
                 caption=item_instance.caption, amount=item_json['amount'])

        return super().try_activate(player, amount, async)

register_item_instance_class('gift', Gift)
