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

from ...resource.strings import build_module_strings

from ..arcjail.arcjail_user import arcjail_user_manager

from . import earn_credits


strings_module = build_module_strings('credits/server_command')


@ServerCommand('arcjail_add_credits')
def server_arcjail_add_credits(command):
    try:
        userid = command[1]
        credits = command[2]
    except IndexError:
        echo_console("Usage: arcjail_add_credits <userid> <credits>")
        return

    try:
        userid = int(userid)
    except ValueError:
        echo_console("Error: userid should be an integer")
        return

    try:
        credits = int(credits)
    except ValueError:
        echo_console("Error: credits should be an integer")
        return

    try:
        arcjail_user = arcjail_user_manager.get_by_userid(userid)
        if arcjail_user is None:
            raise KeyError
    except (KeyError, OverflowError, ValueError):
        echo_console("Couldn't find ArcjailUser (userid={})".format(userid))
        return

    earn_credits(arcjail_user.player, credits, strings_module['reason'])
    echo_console("Added {} credits to {}'s account".format(
        credits, arcjail_user.player.name))
