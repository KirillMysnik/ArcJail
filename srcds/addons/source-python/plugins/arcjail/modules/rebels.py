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
from events import Event
from filters.players import PlayerIter
from filters.entities import EntityIter
from listeners.tick import Delay

from mathlib import NULL_VECTOR

from controlled_cvars.handlers import (bool_handler, color_handler,
                                       list_handler, sound_handler)

from ..internal_events import InternalEvent
from ..resource.strings import build_module_strings

from . import build_module_config
from .admin import section
from .player_colors import cancel_color_request, make_color_request
from .players import broadcast, player_manager
from .skins import model_player_manager
from .teams import GUARDS_TEAM, PRISONERS_TEAM


strings_module = build_module_strings('rebels')
config_manager = build_module_config('rebels')


config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable rebels tracking",
)
config_manager.controlled_cvar(
    list_handler,
    "forbidden_weapons",
    default="ak47,aug,awp,famas,g3sg1,galil,m249,m3,m4a1,mac10,mp5navy,"
            "p90,scout,sg550,sg552,tmp,ump45,xm1014",
    description="List of weapons that will cause prisoner to become a "
                "rebel on pickup, separated by comma",
)
config_manager.controlled_cvar(
    list_handler,
    "soft_weapons",
    default="flashbang,smokegrenade",
    description="List of weapons that will NOT cause prisoner to become a "
                "rebel on attack, separated by comma",
)
config_manager.controlled_cvar(
    bool_handler,
    "drop_hot_weapons",
    default=1,
    description="Enable/Disable automatically dropping weapons from "
                "forbidden list on pickup",
)
config_manager.controlled_cvar(
    color_handler,
    "rebel_color",
    default="200,0,0",
    description="Colors for rebelling prisoners - Red,Green,Blue. "
                "E.g. 200,0,0.",
)
config_manager.controlled_cvar(
    bool_handler,
    "prefer_model_over_color",
    default=1,
    description="Enable/Disable marking rebels with a model "
                "(<rebel_model>) instead of color (<rebel_color>)",
)
config_manager.controlled_cvar(
    bool_handler,
    "forbid_stashes",
    default=0,
    description="Defines whether prisoner will automatically be "
                "considered rebel on entering any kind of stash",
)
config_manager.controlled_cvar(
    bool_handler,
    "forbid_armory",
    default=1,
    description="Defines whether prisoner will automatically be "
                "considered rebel on entering armory",
)
config_manager.controlled_cvar(
    sound_handler,
    name="rebel_sound",
    default="arcjail/rebel.mp3",
    description="Sound to play to prisoner when they become a rebel",
)
config_manager.controlled_cvar(
    bool_handler,
    "hide_knife",
    default=1,
    description="Enable/Disable invisible knife for non-rebelling "
                "prisoners",
)


# How many seconds a weapon should be considered hot for
HOT_WEAPON_TIMEOUT = 1.5

# Whether or not we ignore map creator's views on weapon condition
IGNORE_MAP_REBELWEAPONS = False

SKIN_PRIORITY = 3


_rebels = set()
_filters = []
_round_end = False
_hot_weapons = {}


def _set_rebel(player):
    _rebels.add(player)

    if config_manager['prefer_model_over_color']:
        model_player_manager[player.index].make_request(
            'rebels', SKIN_PRIORITY, "rebel")

    else:
        make_color_request(
            player, SKIN_PRIORITY, 'rebels', config_manager['rebel_color'])

    # TODO: flash
    # TODO: sound

    InternalEvent.fire('jail_rebel_set', player=player)


def _unset_rebel(player):
    _rebels.discard(player)

    cancel_color_request(player, 'rebels')
    model_player_manager[player.index].cancel_request('rebels')

    InternalEvent.fire('jail_rebel_unset', player=player)


def _can_rebel(player):
    # 1. Check if we're enabled
    if not config_manager['enabled']:
        return False

    # 2. If round is over, they can't rebel
    if _round_end:
        return False

    # 3. Only prisoners can rebel
    if player.team != PRISONERS_TEAM:
        return False

    # 4. They can't rebel twice
    if player in _rebels:
        return False

    # 5. Go through filters
    for filter_ in _filters:
        if filter_(player) is False:
            return False

    # Note: we don't check if a player is alive or not
    return True


def is_rebel(player):
    """ Return True if given player is a rebel. """
    return player in _rebels


def set_rebel(player):
    """ Set given player as a rebel (with all checks). """
    if _can_rebel(player) and not player.dead:
        _set_rebel(player)


def unset_rebel(player):
    """ Unset given player as a rebel (with all checks). """
    if is_rebel(player):
        _unset_rebel(player)


def reset_rebels():
    """ Reset rebels list. """
    InternalEvent.fire('jail_rebels_reset')
    for rebel in set(_rebels):
        _unset_rebel(rebel)


def iter_rebels():
    """ Iter over all rebels (player instances). """
    return iter(_rebels)


def get_rebels():
    return tuple(_rebels)


def register_rebel_filter(filter_):
    """ Register new rebel filter. """
    if filter_ in _filters:
        raise ValueError("Filter '%s' is already registered" % filter_)
    _filters.append(filter_)


def unregister_rebel_filter(filter_):
    """ Unregister given rebel filter. """
    _filters.remove(filter_)


def mark_weapon_hot(entity):
    if entity.index in _hot_weapons:
        _hot_weapons[entity.index].cancel()

    def cool_weapon(entity=entity):
        _hot_weapons.pop(entity.index, None)

    _hot_weapons[entity.index] = Delay(HOT_WEAPON_TIMEOUT, cool_weapon)


@Event('player_death_real')
def on_player_death_real(game_event):
    player = player_manager.get_by_userid(game_event['userid'])

    if player not in _rebels:
        return

    _unset_rebel(player)

    aid = game_event['attacker']
    if aid == player.userid or not aid:
        broadcast(strings_module['suicide'].tokenize(rebel=player.name))
        InternalEvent.fire('jail_rebel_suicide',
                           player=player,
                           game_event=game_event)
    else:
        InternalEvent.fire('jail_rebel_killed',
                           player=player,
                           game_event=game_event)


@Event('player_hurt')
def on_player_hurt(game_event):
    player = player_manager.get_by_userid(game_event['userid'])

    # Only able rebel against guards
    if player.team != GUARDS_TEAM:
        return

    # They don't rebel if, say, flashbang was used
    if game_event['weapon'] in config_manager['soft_weapons']:
        return

    aid = game_event['attacker']
    # World- and self-damage won't count
    if aid == player.userid or not aid:
        return

    attacker = player_manager.get_by_userid(aid)
    # Further checks on attacker
    if not _can_rebel(attacker):
        return

    if attacker.dead:
        InternalEvent.fire(
            'jail_posthumous_rebel',
            player=player,
            attacker=attacker,
            game_event=game_event,
        )
        broadcast(strings_module['posthumous'].tokenize(rebel=attacker.name))
    else:
        _set_rebel(attacker )
        broadcast(strings_module['by_attack'].tokenize(
            victim=player.name,
            rebel=attacker.name,
        ))


@Event('item_pickup')
def on_item_pickup(game_event):
    def does_weapon_trigger_rebel(player, weapon_class, entity):
        should_rebel = weapon_class[7:] in config_manager['forbidden_weapons']

        if IGNORE_MAP_REBELWEAPONS:
            return should_rebel
        # ArcJail allows mapmakers to decide if a picked weapon:
        # 1 - should always make its owner a rebel
        # 0 - should never make its owner a rebel
        # -1 - doesn't have any particular restrictions (server default)
        try:
            # TODO: Extract 'rebelsweapon' keyvalue from entity
            mapmaker_opinion = -1
        except:
            mapmaker_opinion = -1

        return (mapmaker_opinion == -1 and should_rebel or
                mapmaker_opinion == 1)

    player = player_manager.get_by_userid(game_event['userid'])
    if player.dead or not _can_rebel(player):
        return

    # TODO: Use weapon_manager to get the proper "weapon_" prefix
    weapon_class = 'weapon_{}'.format(game_event['item'])
    for entity in EntityIter(weapon_class):
        if entity.owner_handle == player.inthandle:
            break

    else:
        return

    if does_weapon_trigger_rebel(player, weapon_class, entity):
        if entity.index in _hot_weapons:
            player.drop_weapon(entity.pointer, NULL_VECTOR, NULL_VECTOR)
            mark_weapon_hot(entity)
        else:
            _set_rebel(player)
            broadcast(strings_module['by_pickup'].tokenize(rebel=player.name))


@InternalEvent('player_deleted')
def on_player_deleted(player):
    _rebels.discard(player)


@Event('round_start')
def on_round_start(game_event):
    reset_rebels()

    global _round_end
    _round_end = False


@Event('round_end')
def on_round_end(game_event):
    global _round_end
    _round_end = True


@InternalEvent('load')
def on_load():
    is_rebel = lambda player: player in _rebels
    PlayerIter.register_filter('jail_rebel', is_rebel)


@InternalEvent('unload')
def on_unload():
    PlayerIter.unregister_filter('jail_rebel')


@ClientCommand('drop')
def cmd_on_drop(command, index):
    if not config_manager['drop_hot_weapons']:
        return

    player = player_manager[index]
    if not (player.team == GUARDS_TEAM or is_rebel(player)):
        return True

    weapons = []
    for entity in EntityIter():
        if not entity.classname.startswith('weapon_'):
            continue

        if entity.owner_handle == player.inthandle:
            weapons.append(entity)

    def confirm_weapon_drop():
        for entity in weapons:
            if entity.owner_handle == player.inthandle:
                continue

            mark_weapon_hot(entity)

    Delay(0, confirm_weapon_drop)

    return True


# =============================================================================
# >> ARCADMIN ENTRIES
# =============================================================================
if section is not None:
    from arcadmin.classes.menu import PlayerBasedCommand, Section

    class ToggleRebelCommand(PlayerBasedCommand):
        base_filter = ('jail_prisoner', 'alive')
        include_equal_priorities = False

        @staticmethod
        def player_name(player):
            if is_rebel(player):
                return strings_module['arcadmin name_prefix'].tokenize(
                    base=player.name)
            return player.name

        @staticmethod
        def player_select_callback(admin, players):
            for player in players:
                if is_rebel(player):
                    unset_rebel(player)
                    admin.announce(strings_module['arcadmin unset'].tokenize(
                        rebel=player.name))

                else:
                    set_rebel(player)
                    admin.announce(strings_module['arcadmin set'].tokenize(
                        rebel=player.name))

    rebels_section = section.add_child(
        Section, strings_module['arcadmin section'])

    rebels_section.add_child(
        ToggleRebelCommand, strings_module['arcadmin option toggle_rebel'],
        'jail.rebels.toggle', 'toggle'
    )
