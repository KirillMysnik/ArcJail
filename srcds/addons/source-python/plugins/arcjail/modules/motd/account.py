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

from commands.say import SayCommand

from ..arcjail import strings_module as strings_arcoins
from ..arcjail.arcjail_user import arcjail_user_manager

from ..players import main_player_manager, tell


from . import plugin_instance


def send_page(player):
    arcjail_user = arcjail_user_manager[player.index]
    if not arcjail_user.loaded:
        tell(player, strings_arcoins['not synced'])
        return

    def account_callback(data, error):
        pass

    def json_account_callback(data, error):
        if error is not None:
            return

        if data['action'] != "init":
            return

        return {
            'account': "{:,}".format(arcjail_user.account),
        }

    def account_retargeting_callback(new_page_id):
        if new_page_id == "json-account":
            return json_account_callback, json_account_retargeting_callback

    def json_account_retargeting_callback(new_page_id):
        return None

    plugin_instance.send_page(
        player, 'account', account_callback, account_retargeting_callback)


@SayCommand('!account')
def say_account(command, index, team_only):
    player = main_player_manager[index]
    send_page(player)
