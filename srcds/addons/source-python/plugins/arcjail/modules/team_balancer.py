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

from commands.client import ClientCommand
from engines.server import engine_server
from events import Event
from messages import TextMsg, VGUIMenu
from players.teams import teams_by_name

from controlled_cvars import InvalidValue
from controlled_cvars.handlers import bool_handler, sound_nullable_handler

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings

from .game_status import GameStatus, set_status

from .teams import PRISONERS_TEAM, GUARDS_TEAM

from .players import broadcast, main_player_manager

from . import build_module_config


strings_module = build_module_strings('team_balancer')
config_manager = build_module_config('team_balancer')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable team balancing",
)


def ratio_handler(cvar):
    try:
        val = float(cvar.get_string())
    except ValueError:
        raise InvalidValue

    if val < 0:
        raise InvalidValue

    return val

config_manager.controlled_cvar(
    ratio_handler,
    "min_ratio",
    default=2.5,
    description="No less than <value> prisoners per 1 guard",
)
config_manager.controlled_cvar(
    ratio_handler,
    "max_ratio",
    default=5,
    description="No more than <value> prisoners per 1 guard",
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "deny_sound",
    default="buttons\weapon_cant_buy.wav",
    description="Sound to play when player tries to join unavailable team",
)


INF = float('inf')
SPECTATORS_TEAM = teams_by_name['spec']


def count_teams():
    num_prisoners = num_guards = 0
    for player in main_player_manager.values():
        if player.team == PRISONERS_TEAM:
            num_prisoners += 1
        elif player.team == GUARDS_TEAM:
            num_guards += 1
    return num_prisoners, num_guards


class ImbalanceCase:
    BALANCED = 1
    NEED_MORE_PRISONERS = 2
    NEED_MORE_GUARDS = 3


def check_teams(num_prisoners, num_guards):
    rmin = max(0, config_manager['min_ratio'])
    rmax = config_manager['max_ratio']

    if (num_guards == 0) or (num_prisoners / num_guards > rmax):
        return ImbalanceCase.NEED_MORE_GUARDS

    if num_prisoners / num_guards < rmin:
        return ImbalanceCase.NEED_MORE_PRISONERS

    return ImbalanceCase.BALANCED


class SwapDirection:
    MORE_PRISONERS = 1
    MORE_GUARDS = 2


def check_swap(num_prisoners, num_guards, swap_direction):
    state = check_teams(num_prisoners, num_guards)
    if state == ImbalanceCase.BALANCED:
        return True

    if (state == ImbalanceCase.NEED_MORE_PRISONERS and
                swap_direction == SwapDirection.MORE_PRISONERS):

        return True

    if (state == ImbalanceCase.NEED_MORE_GUARDS and
                swap_direction == SwapDirection.MORE_GUARDS):
        return True

    return False


def deny(player):
    if config_manager['deny_sound'] is not None:
        config_manager['deny_sound'].play(player.index)


def reset_cvars():
    engine_server.server_command("mp_limitteams 0;")
    engine_server.server_command("mp_autoteambalance 0;")


def show_team_selection(player):
    VGUIMenu('team', show=True).send(player.index)


_locked = 0


def lock_teams():
    global _locked
    _locked += 1


def unlock_teams():
    global _locked
    _locked = max(0, _locked - 1)


@InternalEvent('load')
def on_load(arc_event):
    reset_cvars()


@Event('player_team')
def on_player_team(game_event):
    if _locked:
        return

    if check_teams(*count_teams()):
        return

    broadcast(strings_module['imbalance'])


@Event('round_start')
def on_round_start(game_event):
    reset_cvars()


@InternalEvent('jail_game_status_reset')
def on_jail_game_status_reset(event_var):
    if check_teams(*count_teams()) == ImbalanceCase.BALANCED:
        set_status(GameStatus.FREE)
    else:
        broadcast(strings_module['imbalance'])


@ClientCommand('jointeam')
def cl_jointeam(command, index):
    # TODO: premium_base.is_premium support

    # Deny empty args
    if len(command) < 2:
        return False

    player = main_player_manager[index]

    # Deny invalid args
    try:
        new_team = int(command[1])
    except ValueError:
        return False

    # Deny joining the same team, with the exception made
    # for unassigned (team 0) players trying to use auto-assign (team 0)
    if player.team == new_team != 0:
        deny(player)
        TextMsg(strings_module['denied_your_team']).send(index)
        show_team_selection(player)
        return False

    # Always allow switching to spectators
    if new_team == SPECTATORS_TEAM:
        return True

    # Deny switching teams while teams are locked
    # (e.g. Last Request in progress)
    if _locked:
        deny(player)
        TextMsg(strings_module['denied_locked']).send(index)
        return False

    # We count team members as if player has already left their team
    num_prisoners, num_guards = count_teams()
    if player.team == PRISONERS_TEAM:
        num_prisoners -= 1
    elif player.team == GUARDS_TEAM:
        num_guards -= 1

    # Emulate auto-assign: try to send them to guards,
    # and if that's impossible - send them to prisoners
    if new_team == 0:
        can_go_guards = check_swap(
            num_prisoners, num_guards + 1, SwapDirection.MORE_GUARDS)

        if can_go_guards:
            if player.team != GUARDS_TEAM:
                player.team = GUARDS_TEAM
        else:
            if player.team != PRISONERS_TEAM:
                player.team = PRISONERS_TEAM

        # Suppress default auto-assigning behavior
        return False

    if new_team == PRISONERS_TEAM:
        can_go_guards = check_swap(
            num_prisoners, num_guards + 1, SwapDirection.MORE_GUARDS)

        can_go_prisoners = check_swap(
            num_prisoners + 1, num_guards, SwapDirection.MORE_PRISONERS)

        if can_go_guards and not can_go_prisoners:
            deny(player)
            TextMsg(strings_module['denied_balance']).send(index)
            show_team_selection(player)
            return False

        return True

    if new_team == GUARDS_TEAM:
        can_go_guards = check_swap(
            num_prisoners, num_guards + 1, SwapDirection.MORE_GUARDS)

        if can_go_guards:
            return True

        deny(player)
        TextMsg(strings_module['denied_balance']).send(index)
        show_team_selection(player)
        return False

    # Deny non-existing team numbers
    return False
