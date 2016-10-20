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

from ...internal_events import InternalEvent
from ...resource.strings import build_module_strings

from . import credits_config, earn_credits


strings_module = build_module_strings('credits/game_win_reward')


@InternalEvent('jail_game_cock_fight_winners')
def on_jail_game_cock_fight_winners(winners, starting_player_number):
    payout = int(
        int(credits_config['rewards']['cock_fight_win']) *
        (1 - len(winners) / starting_player_number)
    )

    for winner in winners:
        earn_credits(winner, payout, strings_module['reason cock_fight'])


@InternalEvent('jail_game_chat_game_winner')
def on_jail_game_chat_game_winner(winner):
    earn_credits(
        winner, int(credits_config['rewards']['chat_game_win']),
        strings_module['reason chat_game'])


@InternalEvent('jail_game_map_game_team_based_winners')
def on_jail_game_map_game_team_based_win(
        winners, num_teams, starting_player_number, team_num):

    payout = int(credits_config['rewards']['map_game_team_based_win'])

    for winner in winners:
        earn_credits(
            winner, payout, strings_module['reason map_game_team_based'])


@InternalEvent('jail_game_map_game_winners')
def on_jail_game_map_game_winners(winners, starting_player_number):
    payout = int(
        int(credits_config['rewards']['cock_fight_win']) *
        (1 - len(winners) / starting_player_number)
    )

    for winner in winners:
        earn_credits(winner, payout, strings_module['reason map_game'])
