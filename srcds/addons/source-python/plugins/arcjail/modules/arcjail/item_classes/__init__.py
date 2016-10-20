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

from collections import OrderedDict
import json

from ....resource.paths import ARCJAIL_DATA_PATH


registered_item_instance_classes = {}

with open(ARCJAIL_DATA_PATH / 'items.json') as f:
    items_json = json.load(f)

with open(ARCJAIL_DATA_PATH / 'item-categories.json') as f:
    item_categories_json = json.load(f)


def register_item_instance_class(class_id, item_instance_class):
    registered_item_instance_classes[class_id] = item_instance_class


def unregister_item_instance_class(class_id):
    del registered_item_instance_classes[class_id]


import os

from ... import parse_modules


current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)

from . import *


item_classes = OrderedDict()
for category_id, category in sorted(
        item_categories_json.items(), key=lambda items: items[1]['position']):

    if category_id == "all":
        continue

    for class_id in category['class_ids']:
        if class_id in item_classes:
            continue

        class_config = items_json[class_id]
        item_classes[class_id] = {}
        item_instance_class = registered_item_instance_classes[class_id]
        for instance_id, instance_config in class_config.items():
            item_classes[class_id][instance_id] = item_instance_class(
                class_id, instance_id, instance_config, category_id)


def get_item_instance(class_id, instance_id):
    return item_classes.get(class_id, {}).get(instance_id)


def iter_item_instance_classes():
    for item_instances in item_classes.values():
        yield from item_instances.values()
