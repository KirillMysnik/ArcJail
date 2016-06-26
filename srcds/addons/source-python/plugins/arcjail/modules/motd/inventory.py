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
from ..arcjail.item_classes import get_item_instance

from ..players import tell

from . import plugin_instance


def send_page(player):
    arcjail_user = arcjail_user_manager[player.index]
    if not arcjail_user.loaded:
        tell(player, strings_arcjail['not_synced'])
        return

    def inventory_callback(data, error):
        pass

    def json_inventory_callback(data, error):
        from ..shop import config_manager, strings_module as strings_shop

        if error is not None:
            return

        language = get_client_language(player.index)
        popup_notify = popup_error = None

        if data['action'] == "use":
            class_id = data['class_id']
            instance_id = data['instance_id']

            item_instance = get_item_instance(class_id, instance_id)

            # Is it known item?
            if item_instance is None:
                return {'error': "APPERR_UNKNOWN_ITEM"}

            if not item_instance.manual_activation:
                return {'error': "APPERR_NO_MANUAL_ACTIVATION"}

            if player.team not in item_instance.use_team_restriction:
                return {'error': "APPERR_WRONG_TEAM"}

            item = arcjail_user.get_item_by_instance_id(
                class_id, instance_id)

            if item is None:
                return {'error': "APPERR_DOES_NOT_BELONG_TO_PLAYER"}

            reason = item_instance.try_activate(player, item.amount - 1)
            if reason is not None:
                popup_error = reason

            else:
                arcjail_user.take_item(item, amount=1, async=False)

                popup_notify = strings_shop[
                    'popup_notify activated'].tokenize(
                        caption=item.class_.caption)

        inventory_items = []

        # Inventory
        for item in arcjail_user.iter_all_items():
            item_json = {
                'class_id': item.class_.class_id,
                'instance_id': item.class_.instance_id,
                'caption': item.class_.caption.get_string(language),
                'description': item.class_.description.get_string(language),
                'icon': item.class_['icon'],
                'amount': item.amount,
                'cannot_use_reason': None,
            }

            # Does player's team fit requirements?
            if player.team not in item.class_.team_restriction:
                item_json['cannot_use_reason'] = \
                    strings_shop['cannot_buy team_restriction'].get_string(
                        language)

            # Does this item allow manual activation?
            if not item.class_.manual_activation:
                item_json['cannot_use_reason'] = \
                    strings_shop['cannot_use no_manual_activation'].get_string(
                        language)

            # Get stat values
            for stat_name in ('stat_max_per_slot',
                              'stat_team_restriction',
                              'stat_manual_activation',
                              'stat_auto_activation',
                              'stat_max_sold_per_round',
                              'stat_price'):

                stat = getattr(item.class_, stat_name)
                if stat is None:
                    item_json[stat_name] = None
                else:
                    item_json[stat_name] = stat.get_string(language)

            inventory_items.append(item_json)

        if popup_notify is not None:
            popup_notify = popup_notify.get_string(language)

        if popup_error is not None:
            popup_error = popup_error.get_string(language)

        return {
            'account': arcjail_user.account,
            'account_formatted': "{:,}".format(arcjail_user.account),
            'inventory_items': inventory_items,
            'popup_notify': popup_notify,
            'popup_error': popup_error,
        }

    def inventory_retargeting_callback(new_page_id):
        if new_page_id == "json-shop":
            return json_inventory_callback, json_inventory_retargeting_callback

    def json_inventory_retargeting_callback(new_page_id):
        return None

    plugin_instance.send_page(player, 'inventory', inventory_callback,
                              inventory_retargeting_callback)
