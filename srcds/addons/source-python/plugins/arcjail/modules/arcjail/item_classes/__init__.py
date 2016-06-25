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

from ....resource.paths import ARCJAIL_DATA_PATH


registered_item_instance_classes = {}

with open(ARCJAIL_DATA_PATH / 'items.json') as f:
    items_json = load(f)


def register_item_instance_class(class_id, item_instance_class):
    registered_item_instance_classes[class_id] = item_instance_class


def unregister_item_instance_class(class_id):
    del registered_item_instance_classes[class_id]


import os

from ... import parse_modules


current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)

from . import *


item_classes = {}
for class_id, class_config in items_json.items():
    item_classes[class_id] = {}
    item_instance_class = registered_item_instance_classes[class_id]
    for instance_id, instance_config in class_config.items():
        item_classes[class_id][instance_id] = item_instance_class(
            class_id, instance_id, instance_config)


def get_item_instance(class_id, instance_id):
    return item_classes.get(class_id, {}).get(instance_id)


def iter_item_instance_classes():
    for item_instances in item_classes.values():
        yield from item_instances.values()
