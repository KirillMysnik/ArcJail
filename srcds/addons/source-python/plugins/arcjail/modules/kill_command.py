from commands.say import SayCommand

from controlled_cvars.handlers import bool_handler, float_handler

from ..resource.strings import build_module_strings

from .players import broadcast, main_player_manager, tell

from .teams import GUARDS_TEAM, PRISONERS_TEAM

from . import build_module_config


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


@SayCommand("!suicide")
@SayCommand("!kill")
def say_kill(command, index, team_only):
    player = main_player_manager[index]

    reason = get_kill_denial_reason(player)
    if reason is not None:
        tell(player, reason)
        return

    player.push(0, config_manager['vertical_force'], vert_override=True)
    player.take_damage(player.health + 1)
    broadcast(strings_module['slayed'], player=player.name)
