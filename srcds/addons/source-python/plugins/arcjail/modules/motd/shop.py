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

from players.helpers import get_client_language

from ..arcjail import strings_module as strings_arcjail
from ..arcjail.arcjail_user import arcjail_user_manager

from ..players import tell

from . import plugin_instance


def send_page(player):
    from ..shop import (
        get_player_item, give_item_to_player, registered_item_classes,
        take_item_from_player)

    arcjail_user = arcjail_user_manager[player.index]
    if not arcjail_user.loaded:
        tell(player, strings_arcjail['not synced'])
        return

    def shop_callback(data, error):
        pass

    def json_shop_callback(data, error):
        from ..shop import get_all_player_items, strings_module as strings_shop

        if error is not None:
            return

        if data['action'] == "buy":
            item_id = data['item_id']

            # Is it known item?
            if item_id not in registered_item_classes:
                return {}

            # Does player have enough credits to buy it?
            item_class = registered_item_classes[item_id]
            if item_class.price > arcjail_user.account:
                return {}

            # Maybe players already has too many of these items?
            item = get_player_item(player, item_id)
            amount = 0 if item is None else item.amount

            if amount >= item_class.max_per_slot:
                return {}

            # Does player's team fit requirements?
            if player.team not in item_class.team_restriction:
                return {}

            # Ok, let's sell it
            arcjail_user.account -= item_class.price
            item = give_item_to_player(player, item_id)

            if item_class.auto_activation:
                item = take_item_from_player(player, item_id)
                item.activate()

        shop_items = []
        inventory_items = []
        language = get_client_language(player.index)

        # Shop
        for item_class in registered_item_classes.values():
            item_json = {
                'id': item_class.id,
                'caption': item_class.caption.get_string(language),
                'description': item_class.description.get_string(language),
                'price': item_class.price,
                'icon': item_class.icon,
                'cannot_buy_reason': None,
            }

            # Maybe players already has too many of these items?
            item = get_player_item(player, item_class.id)
            amount = 0 if item is None else item.amount

            if amount >= item_class.max_per_slot:
                item_json['cannot_buy_reason'] = \
                    strings_shop['cannot_buy max_per_slot'].get_string(
                        language)

            # Does player's team fit requirements?
            if player.team not in item_class.team_restriction:
                item_json['cannot_buy_reason'] = \
                    strings_shop['cannot_buy team_restriction'].get_string(
                        language)

            # Get stat values
            for stat_name in ('stat_max_per_slot',
                              'stat_team_restriction',
                              'stat_manual_activation',
                              'stat_auto_activation',
                              'stat_max_sold_per_round',
                              'stat_price',
                              ):

                stat = getattr(item_class, stat_name)()
                if stat is None:
                    item_json[stat_name] = None
                else:
                    item_json[stat_name] = stat.get_string(language)

            shop_items.append(item_json)

        # Inventory
        for item in get_all_player_items(player):
            item_json = {
                'id': item.id,
                'caption': item.caption.get_string(language),
                'description': item.description.get_string(language),
                'icon': item.icon,
                'cannot_use_reason': None,
            }

            # Does player's team fit requirements?
            if player.team not in item.team_restriction:
                item_json['cannot_use_reason'] = \
                    strings_shop['cannot_buy team_restriction'].get_string(
                        language)

            # Does this item allow manual activation?
            if not item.manual_activation:
                item_json['cannot_use_reason'] = \
                    strings_shop['cannot_use no_manual_activation'].get_string(
                        language)

            # Get stat values
            for stat_name in ('stat_max_per_slot',
                              'stat_team_restriction',
                              'stat_manual_activation',
                              'stat_auto_activation',
                              'stat_max_sold_per_round',
                              'stat_price',
                              ):

                stat = getattr(item, stat_name)()
                if stat is None:
                    item_json[stat_name] = None
                else:
                    item_json[stat_name] = stat.get_string(language)

            inventory_items.append(item_json)

        return {
            'account': arcjail_user.account,
            'account_formatted': "{:,}".format(arcjail_user.account),
            'shop_items': shop_items,
            'inventory_items': inventory_items,
        }

    def shop_retargeting_callback(new_page_id):
        if new_page_id == "json-shop":
            return json_shop_callback, json_shop_retargeting_callback

    def json_shop_retargeting_callback(new_page_id):
        return None

    plugin_instance.send_page(
        player, 'shop', shop_callback, shop_retargeting_callback)
