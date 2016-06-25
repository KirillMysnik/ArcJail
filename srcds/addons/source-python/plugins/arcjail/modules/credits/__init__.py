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

from configparser import ConfigParser

from events import Event
from listeners import OnClientDisconnect

from ...resource.paths import ARCJAIL_DATA_PATH
from ...resource.strings import build_module_strings

from ..arcjail.arcjail_user import arcjail_user_manager
from ..players import main_player_manager, tell


strings_module = build_module_strings('credits/common')
credits_earned_storage = {}
credits_spent_storage = {}

CREDITS_CONFIG_FILE = ARCJAIL_DATA_PATH / "credits.ini"

credits_config = ConfigParser()
credits_config.read(CREDITS_CONFIG_FILE)


def earn_credits(player, credits, reason):
    arcjail_user = arcjail_user_manager[player.index]
    if not arcjail_user.loaded:
        return

    credits_earned_storage[player.index] = credits_earned_storage.get(
        player.index, 0) + credits

    arcjail_user.account += credits

    tell(player, strings_module['credits_earned'],
         credits=credits, reason=reason)


def spend_credits(player, credits, reason):
    arcjail_user = arcjail_user_manager[player.index]
    if not arcjail_user.loaded:
        return

    credits_spent_storage[player.index] = credits_spent_storage.get(
        player.index, 0) + credits

    arcjail_user.account -= credits

    tell(player, strings_module['credits_paid'],
         credits=credits, reason=reason)


@OnClientDisconnect
def listener_on_client_disconnect(index):
    for dict_ in (credits_earned_storage, credits_spent_storage):
        if index in dict_:
            del dict_[index]


@Event('round_start')
def on_round_start(game_event):
    for index, arcjail_user in arcjail_user_manager.items():
        if not arcjail_user.loaded:
            continue

        credits_earned_storage[index] = 0
        credits_spent_storage[index] = 0


@Event('round_end')
def on_round_end(game_event):
    for index, credits_earned in credits_earned_storage.items():
        credits_spent = credits_spent_storage[index]

        player = main_player_manager[index]
        tell(player, strings_module['credits_diff_round'],
             plus=credits_earned, minus=credits_spent)


import os

from .. import parse_modules


current_dir = os.path.dirname(__file__)
__all__ = parse_modules(current_dir)


from . import *
