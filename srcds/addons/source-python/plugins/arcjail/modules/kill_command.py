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

from spam_proof_commands.say import SayCommand

from controlled_cvars.handlers import bool_handler, float_handler

from ..resource.strings import build_module_strings

from .players import broadcast, main_player_manager, tell

from .teams import GUARDS_TEAM, PRISONERS_TEAM

from . import build_module_config


ANTI_SPAM_TIMEOUT = 1


strings_module = build_module_strings('kill_command')
config_manager = build_module_config('kill_command')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable !kill chat command",
)
config_manager.controlled_cvar(
    float_handler,
    "vertical_force",
    default=1000.0,
    description="Vertical force to apply to a player when killing them",
)


def get_kill_denial_reason(player):
    if not config_manager['enabled']:
        return strings_module['fail_disabled']

    if player.dead:
        return strings_module['fail_dead']

    if player.team not in (GUARDS_TEAM, PRISONERS_TEAM):
        return strings_module['fail_wrong_team']

    return None


@SayCommand(ANTI_SPAM_TIMEOUT, ["!suicide", "!kill"])
def say_kill(command, index, team_only):
    player = main_player_manager[index]

    reason = get_kill_denial_reason(player)
    if reason is not None:
        tell(player, reason)
        return

    player.push(0, config_manager['vertical_force'], vert_override=True)
    player.take_damage(player.health + 1)
    broadcast(strings_module['slayed'], player=player.name)
