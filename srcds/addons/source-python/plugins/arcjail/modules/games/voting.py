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

from random import choice

from listeners.tick import Delay
from menus import PagedMenu, PagedOption

from controlled_cvars.handlers import float_handler

from ...arcjail import InternalEvent

from ...resource.strings import build_module_strings

from .. import build_module_config

from ..jail_menu import new_available_option

from ..players import broadcast, main_player_manager, tell

from . import (
    get_available_launchers, get_game_denial_reason, get_players_to_play)


strings_module = build_module_strings('games/voting')
config_manager = build_module_config('games/voting')

config_manager.controlled_cvar(
    float_handler,
    "timeout",
    default=15.0,
    description="How much time the games voting should last for"
)

_last_voting = None


class GameVoting(dict):
    def __init__(self):
        super().__init__()

        self._votes_received = 0
        self._max_players = -1
        self._timeout_delay = None
        self._popup = None
        self.result = None

    def select_callback(self, popup, index, option):
        self._votes_received += 1

        if option.value != "WONT_PLAY":
            self[option.value] = self.get(option.value, 0) + 1

            player = main_player_manager[index]
            broadcast(strings_module['player_voted'].tokenize(
                player=player.name, choice=option.value.caption))

        if self._votes_received >= self._max_players:
            self.finish()

    def start(self, popup, targets, timeout):
        self._popup = popup
        self._max_players = len(targets)
        self._timeout_delay = Delay(timeout, self.finish)

        popup.send(*[player.index for player in targets])

    def finish(self):
        if self._popup is None:
            return

        if self._timeout_delay is not None:
            if self._timeout_delay.running:
                self._timeout_delay.cancel()

            self._timeout_delay = None

        self._popup.close()
        self._popup = None

        if not self:
            broadcast(strings_module['result no_game'])
            InternalEvent.fire('jail_games_voting_result', result=None)
            return

        top_games = sorted(
            self.keys(), key=lambda key: self[key], reverse=True)

        top_score = self[top_games[0]]
        top_games = list(filter(lambda key: self[key] == top_score, top_games))
        winner = choice(top_games)

        self.result = winner
        broadcast(strings_module['result chosen_game'], caption=winner.caption)
        InternalEvent.fire('jail_games_voting_result', result=winner)

        self.clear()


def launch_voting(player, wont_play_option=False):
    reason = get_game_denial_reason(player)
    if reason is not None:
        tell(player, reason)
        return

    global _last_voting
    if _last_voting is not None:
        _last_voting.finish()

    _last_voting = GameVoting()

    popup = PagedMenu(
        select_callback=_last_voting.select_callback,
        title=strings_module['popup title']
    )

    if wont_play_option:
        popup.append(PagedOption(
            text=strings_module['popup option wont_play'],
            value="WONT_PLAY",
        ))

    players = get_players_to_play()
    for launcher in get_available_launchers(player, players):
        popup.append(PagedOption(
            text=launcher.caption,
            value=launcher,
        ))

    _last_voting.start(popup, players, config_manager['timeout'])


# =============================================================================
# >> JAIL MENU ENTRIES
# =============================================================================
def jailmenu_voting(player):
    launch_voting(player)


def jailmenu_voting_handler_active(player):
    return get_game_denial_reason(player) is None


new_available_option(
    'launch-game-voting',
    strings_module['jailmenu_entry_option'],
    jailmenu_voting,
    handler_active=jailmenu_voting_handler_active,
)
