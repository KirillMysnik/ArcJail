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

from json import load

from ...resource.paths import ARCJAIL_DATA_PATH

from ...resource.strings import build_module_strings

from ..arcjail.arcjail_user import arcjail_user_manager


strings_module = build_module_strings('shop/common')

with open(ARCJAIL_DATA_PATH / 'shop-items.json') as f:
    items_json = load(f)

registered_item_classes = {}


def register_item_class(item_class):
    registered_item_classes[item_class.id] = item_class


def unregister_item_class(item_class):
    del registered_item_classes[item_class.id]


def get_player_item(player, item_id):
    arcjail_user = arcjail_user_manager[player.index]
    if item_id not in arcjail_user.slot_data['items']:
        return None

    item = registered_item_classes[item_id](player)
    item.load_json(arcjail_user.slot_data['items'][item_id])
    return item


def get_all_player_items(player):
    rs = []
    arcjail_user = arcjail_user_manager[player.index]
    for item_id, item_json in arcjail_user.slot_data['items'].items():
        item = registered_item_classes[item_id](player)
        item.load_json(item_json)
        rs.append(item)
    return rs


def give_item_to_player(player, item_id, amount=1):
    arcjail_user = arcjail_user_manager[player.index]

    # Does the item belong to a player yet?
    if item_id in arcjail_user.slot_data['items']:
        item = registered_item_classes[item_id](player)
        item.load_json(arcjail_user.slot_data['items'][item_id])

        # If so, just increase item amount
        item.amount += amount

    else:

        # Otherwise, create a new item of the given amount
        item = registered_item_classes[item_id](player, amount)

    arcjail_user.slot_data['items'][item_id] = item.dump_json()
    return item


def take_item_from_player(player, item_id, amount=1):
    arcjail_user = arcjail_user_manager[player.index]

    item = registered_item_classes[item_id](player)
    item.load_json(arcjail_user.slot_data['items'][item_id])

    item.amount -= amount

    if item.amount <= 0:
        del arcjail_user.slot_data['items'][item_id]
    else:
        arcjail_user.slot_data['items'][item_id] = item.dump_json()

    return item


import os

from .. import parse_modules


current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)


from . import *
from . import item_classes
