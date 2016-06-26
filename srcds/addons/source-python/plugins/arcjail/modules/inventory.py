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

from spam_proof_commands.client import ClientCommand
from spam_proof_commands.say import SayCommand

from menus import PagedMenu, PagedOption
from players.entity import Player

from ..resource.paths import ARCJAIL_DATA_PATH

from ..resource.strings import build_module_strings

from .arcjail.arcjail_user import arcjail_user_manager

from .game_status import GameStatus, get_status

from .motd.inventory import send_page

from .players import tell


ANTI_SPAM_TIMEOUT = 2


strings_module = build_module_strings('inventory')
with open(ARCJAIL_DATA_PATH / 'inventory-ad-lines.json') as f:
    inventory_ad_lines_ids = load(f)


def popup_select_callback(popup, player_index, option):
    item = option.value
    player = item.player

    if get_status() == GameStatus.BUSY:
        tell(player, strings_module['fail game_busy'])
        return

    reason = item.class_.try_activate(player, item.amount - 1, async=True)
    if reason is not None:
        tell(player, strings_module['chat_popup_error'].tokenize(text=reason))

    else:
        arcjail_user = arcjail_user_manager[player.index]
        arcjail_user.take_item(item, amount=1, async=True)

    send_popup(player)


def send_popup(player):
    if get_status() == GameStatus.BUSY:
        tell(player, strings_module['fail game_busy'])
        return

    arcjail_user = arcjail_user_manager[player.index]

    popup = PagedMenu(select_callback=popup_select_callback,
                      title=strings_module['popup title'])

    for item in arcjail_user.iter_all_items():
        if player.team not in item.class_.use_team_restriction:
            continue

        if not item.class_.manual_activation:
            continue

        popup.append(PagedOption(
            text=strings_module['popup entry'].tokenize(
                caption=item.class_.caption, amount=item.amount),
            value=item,
        ))

    if not popup:
        popup.title = strings_module['popup empty_message']

    popup.send(player.index)


@ClientCommand(ANTI_SPAM_TIMEOUT, ['inventory', 'inv'])
@SayCommand(ANTI_SPAM_TIMEOUT, ['!inventory', '!inv'])
def command_inventory(command, index, team_only=None):
    send_page(Player(index))


@ClientCommand(ANTI_SPAM_TIMEOUT, ['inventory_text', 'inv_text'])
@SayCommand(ANTI_SPAM_TIMEOUT, ['!inventory_text', '!inv_text'])
def command_inventory_text(command, index, team_only=None):
    send_popup(Player(index))
