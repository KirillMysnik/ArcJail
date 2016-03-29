from listeners.tick import Delay

from controlled_cvars.handlers import bool_handler, sound_handler

from ..arcjail import InternalEvent, load_downloadables

from .players import main_player_manager

from . import build_module_config


SPAWN_ANNOUNCE_DELAY = 2.0


config_manager = build_module_config('welcome_message')
config_manager.controlled_cvar(
    bool_handler,
    name="enabled",
    default=1,
    description="Enable/Disable welcome messages",
)
config_manager.controlled_cvar(
    sound_handler,
    name="sound",
    default="arcjail/welcome.mp3",
    description="Welcome sound",
)

_announced_uids = {}
_downloads = load_downloadables('welcome-sounds.res')


def announce(player):
    if config_manager['sound'] is not None:
        config_manager['sound'].play(player.index)


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    if player.userid not in _announced_uids:
        _announced_uids[player.userid] = Delay(
            SPAWN_ANNOUNCE_DELAY, announce, player)


@InternalEvent('main_players_loaded')
def on_main_players_loaded(event_var):
    for player in main_player_manager.values():
        _announced_uids[player.userid] = None
        announce(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    if player.userid in _announced_uids:
        if (_announced_uids[player.userid] is not None and
                _announced_uids[player.userid].running):

            _announced_uids[player.userid].cancel()

        del _announced_uids[player.userid]
