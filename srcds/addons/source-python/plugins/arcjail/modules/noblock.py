from commands.say import SayCommand
from events import Event
from filters.players import PlayerIter
from listeners.tick import Delay

from controlled_cvars import bool_handler, float_handler

from ..resource.strings import build_module_strings

from .players import main_player_manager, tell

from .teams import PRISONERS_TEAM

from . import build_module_config


strings_module = build_module_strings('noblock')
config_manager = build_module_config('noblock')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable !noblock chat command. Such command toggles "
                "players' collision relative to its default value.",
)
config_manager.controlled_cvar(
    bool_handler,
    "default",
    default=0,
    description="If enabled, players won't collide with each other by default",
)
config_manager.controlled_cvar(
    float_handler,
    "chat_command_duration",
    default=10.0,
    description="How many seconds to turn on or off player's collisions for "
                "when !noblock command is used",
)


_locked = 0
_delays = {}


def lock():
    global _locked
    _locked += 1


def unlock():
    global _locked
    _locked = max(0, _locked - 1)


def set_force_on(player):
    player.noblock = True


def set_force_off(player):
    player.noblock = False


def set_default(player):
    player.noblock = config_manager['default']


def get_noblock_denial_reason(player):
    if not config_manager['enabled']:
        return strings_module['fail_disabled']

    if player.isdead:
        return strings_module['fail_dead']

    if _locked and player.team == PRISONERS_TEAM:
        return strings_module['fail_locked']

    return None


@Event('round_start')
def on_round_start(game_event):
    for delay in _delays.values():
        delay.cancel()

    _delays.clear()
    unlock()

    for player in PlayerIter('alive'):
        set_default(player)


@SayCommand('!block')
@SayCommand('!noblock')
def say_noblock(command, index, team_only):
    player = main_player_manager.get_by_index(index)
    reason = get_noblock_denial_reason(player)
    if reason:
        tell(player, reason)
        return

    if player.userid in _delays:
        _delays[player.userid].cancel()

    def callback():
        del _delays[player.userid]
        if get_noblock_denial_reason(player):
            return

        if config_manager['default']:
            set_force_on(player)
        else:
            set_force_off(player)

    _delays[player.userid] = Delay(
        config_manager['chat_command_duration'], callback)

    if config_manager['default']:
        set_force_off(player)
        tell(player, '$noblock solid_enabled',
             time=config_manager['chat_command_duration'])
    else:
        set_force_on(player)
        tell(player, '$noblock solid_disabled',
             time=config_manager['chat_command_duration'])
