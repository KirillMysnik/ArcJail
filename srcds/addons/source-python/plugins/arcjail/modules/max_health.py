from ..arcjail import InternalEvent

from . import build_module_config


config_manager = build_module_config('max_health')
cvars = {
    'default_value': config_manager.cvar(
        name="default_value",
        default=100,
        description="Default maximum health for every player",
    ),
}

players = {}


def upgrade_health(player, new_amount):
    """Set player's health to max(<current amount>, new_amount)"""
    player.health = max(player.health, new_amount)


def restore_health(player):
    """Restore player's health to its maximum"""
    player.health = max(player.health, players[player.userid])


def set_max_health(player, amount):
    """Set player's health maximum"""
    players[player.userid] = amount


def upgrade_max_health(player, new_amount):
    """Set player's maximum health to max(<current max health amount>, amount)"""
    players[player.userid] = max(players[player.userid], new_amount)


def get_max_health(player):
    """Return player's health maximum"""
    return players[player.userid]


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    set_max_health(player, cvars['default_value'].get_int())
    restore_health(player)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    set_max_health(event_var['player'], cvars['default_value'].get_int())


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    del players[event_var['player'].userid]
