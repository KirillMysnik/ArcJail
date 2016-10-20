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

import json

from players.helpers import get_client_language

from ...models.arcjail_user import ArcjailUser as DB_ArcjailUser
from ...models.item import Item as DB_Item
from ...resource.sqlalchemy import Session
from ...resource.strings import build_module_strings

from ..admin import section
from ..arcjail.item_classes import item_classes

from . import plugin_instance


strings_module = build_module_strings('superuser')


def send_page(player):
    language = get_client_language(player.index)

    # /su
    def su_callback(data, error):
        pass

    def su_retargeting_callback(new_page_id):
        if new_page_id == "su-offline-items":
            return (su_offline_items_callback,
                    su_offline_items_retargeting_callback)

        if new_page_id == "su-online-items":
            return (su_online_items_callback,
                    su_online_items_retargeting_callback)

        return None

    # /su-offline-items
    def su_offline_items_callback(data, error):
        pass

    def su_offline_items_retargeting_callback(new_page_id):
        if new_page_id == "ajax-su-offline-items":
            return (ajax_su_offline_items_callback,
                    ajax_su_offline_items_retargeting_callback)

        return None

    # /ajax-su-offline-items
    def ajax_su_offline_items_callback(data, error):
        db_session = Session()

        db_arcjail_user = db_session.query(
            DB_ArcjailUser).filter_by(steamid=data['steamid']).first()

        if db_arcjail_user is None:
            db_session.close()

            error = strings_module['su_offline_items steamid_not_found']
            return {
                'popup_error': error.get_string(language),
            }

        if data['action'] == "view-inventory":
            inventory_items = []

            for item_id in json.loads(db_arcjail_user.slot_data):
                db_item = db_session.query(DB_Item).filter_by(
                    id=item_id).first()

                if db_item is None:
                    continue

                item_instance = item_classes[db_item.class_id][
                    db_item.instance_id]

                item_json = {
                    'class_id': item_instance.class_id,
                    'instance_id': item_instance.instance_id,
                    'caption': item_instance.caption.get_string(language),
                    'description': item_instance.description.get_string(
                        language),

                    'icon': item_instance['icon'],
                    'amount': db_item.amount,
                }

                for stat_name in ('stat_max_per_slot',
                                  'stat_team_restriction',
                                  'stat_manual_activation',
                                  'stat_auto_activation',
                                  'stat_max_sold_per_round',
                                  'stat_price'):

                    stat = getattr(item_instance, stat_name)
                    if stat is None:
                        item_json[stat_name] = None
                    else:
                        item_json[stat_name] = stat.get_string(language)

                inventory_items.append(item_json)

            db_session.close()

            notify = strings_module['su_offline_items inventory_loaded']
            return {
                'account': db_arcjail_user.account,
                'account_formatted': "{:,}".format(db_arcjail_user.account),
                'inventory_items': inventory_items,
                'popup_notify': notify.get_string(language),
            }

        if data['action'] == "give-item":
            try:
                item_classes[data['class_id']][data['instance_id']]
            except KeyError:
                db_session.close()

                error = strings_module['su_offline_items unknown_item']
                return {
                    'popup_error': error.get_string(language),
                }

            slot_data = json.loads(db_arcjail_user.slot_data)
            for item_id in slot_data:
                db_item = db_session.query(DB_Item).filter_by(
                    id=item_id).first()

                if db_item is None:
                    continue

                if (db_item.class_id, db_item.instance_id) == (
                        data['class_id'], data['instance_id']):

                    db_item.amount += data['amount']
                    break

            else:
                db_item = DB_Item()
                db_item.class_id = data['class_id']
                db_item.instance_id = data['instance_id']
                db_item.amount = data['amount']
                db_item.current_owner = data['steamid']

                db_session.add(db_item)
                db_session.commit()

                slot_data.append(db_item.id)
                db_arcjail_user.slot_data = json.dumps(slot_data)

            db_session.commit()
            db_session.close()

            notify = strings_module['su_offline_items item_given']
            return {
                'popup_notify': notify.get_string(language),
            }

    def ajax_su_offline_items_retargeting_callback(new_page_id):
        if new_page_id == "su":
            return su_callback, su_retargeting_callback

        return None

    # /su-online-items
    def su_online_items_callback(data, error):
        pass

    def su_online_items_retargeting_callback(new_page_id):
        if new_page_id == "ajax-su-online-items":
            return (ajax_su_online_items_callback,
                    ajax_su_online_items_retargeting_callback)

        return None

    # /ajax-su-online-items
    def ajax_su_online_items_callback(data, error):
        pass   # TODO: Implement

    def ajax_su_online_items_retargeting_callback(new_page_id):
        if new_page_id == "su":
            return su_callback, su_retargeting_callback

        return None

    plugin_instance.send_page(
        player, 'su', su_callback, su_retargeting_callback)


# =============================================================================
# >> ARCADMIN ENTRIES
# =============================================================================
if section is not None:
    from arcadmin.classes.menu import Command

    class SendSuperUserPage(Command):
        @staticmethod
        def select_callback(admin):
            send_page(admin.player)

    section.add_child(SendSuperUserPage, strings_module['arcadmin option su'],
                      'jail.su', 'su-page')
