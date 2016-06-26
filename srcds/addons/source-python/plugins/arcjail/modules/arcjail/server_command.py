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

from commands.server import ServerCommand
from core import echo_console

from ..arcjail.arcjail_user import arcjail_user_manager

from .item_classes import get_item_instance


@ServerCommand('arcjail_give_item')
def server_arcjail_give_item(command):
    try:
        userid = command[1]
        class_id = command[2]
        instance_id = command[3]
        amount = command[4]
    except IndexError:
        echo_console("Usage: arcjail_give_item <userid> <class_id> "
                     "<instance_id> <amount>")
        return

    try:
        userid = int(userid)
    except ValueError:
        echo_console("Error: userid should be an integer")
        return

    item_instance = get_item_instance(class_id, instance_id)
    if item_instance is None:
        echo_console("Couldn't find ItemInstance (class_id={}, "
                     "instance_id={})".format(class_id, instance_id))

        return

    try:
        amount = int(amount)
    except ValueError:
        echo_console("Error: amount should be an integer")
        return

    try:
        arcjail_user = arcjail_user_manager.get_by_userid(userid)
        if arcjail_user is None:
            raise KeyError
    except (KeyError, OverflowError, ValueError):
        echo_console("Couldn't find ArcjailUser (userid={})".format(userid))
        return

    item = arcjail_user.give_item(
        class_id, instance_id, amount=amount, async=False)

    echo_console("Given item ID: {}".format(item.id))
