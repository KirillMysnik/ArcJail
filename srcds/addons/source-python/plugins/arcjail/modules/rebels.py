from commands.client import ClientCommand
from entities.helpers import index_from_inthandle
from events import Event
from filters.players import PlayerIter
from filters.entities import EntityIter
from listeners.tick import Delay

from ..arcjail import InternalEvent

from ..resource.strings import build_module_strings

from .player_colors import cancel_color_request, make_color_request

from .players import broadcast, main_player_manager

from .skins import cancel_model_request, make_model_request

from .teams import GUARDS_TEAM, PRISONERS_TEAM

from . import build_module_config


strings_module = build_module_strings('rebels')

config_manager = build_module_config('rebels')
cvars = {
    'enabled': config_manager.cvar(
        name="enabled",
        default=1,
        description="Enable/Disable rebels tracking",
    ),
    'forbidden_weapons': config_manager.cvar(
        name="forbidden_weapons",
        default="ak47,aug,awp,famas,g3sg1,galil,m249,m3,m4a1,mac10,mp5navy,"
                "p90,scout,sg550,sg552,tmp,ump45,xm1014",
        description="List of weapons that will cause prisoner to become a "
                    "rebel on pickup, separated by comma",
    ),
    'soft_weapons': config_manager.cvar(
        name="soft_weapons",
        default="flashbang,smokegrenade",
        description="List of weapons that will NOT cause prisoner to become a "
                    "rebel on attack, separated by comma",
    ),
    'drop_hot_weapons': config_manager.cvar(
        name="drop_hot_weapons",
        default=1,
        description="Enable/Disable automatically dropping weapons from "
                    "forbidden list on pickup",
    ),
    'rebel_color': config_manager.cvar(
        name="rebel_color",
        default="200,0,0",
        description="Colors for rebelling prisoners - Red,Green,Blue. "
                    "E.g. 200,0,0.",
    ),
    'rebel_model': config_manager.cvar(
        name="rebel_model",
        default="models/player/arcjail/rebel/rebel.mdl",
        description="Model for rebelling prisoners",
    ),
    'prefer_model_over_color': config_manager.cvar(
        name="prefer_model_over_color",
        default=1,
        description="Enable/Disable marking rebels with a model "
                    "(<rebel_model>) instead of color (<rebel_color>)",
    ),
    'forbid_stashes': config_manager.cvar(
        name="forbid_stashes",
        default=0,
        description="Defines whether prisoner will automatically be "
                    "considered rebel on entering any kind of stash",
    ),
    'forbid_armory': config_manager.cvar(
        name="forbid_armory",
        default=1,
        description="Defines whether prisoner will automatically be "
                    "considered rebel on entering armory",
    ),
    'rebel_sound': config_manager.cvar(
        name="rebel_sound",
        default="arcjail/rebel.mp3",
        description="Sound to play to prisoner when they become a rebel",
    ),
    'hide_knife': config_manager.cvar(
        name="hide_knife",
        default=1,
        description="Enable/Disable invisible knife for non-rebelling "
                    "prisoners",
    ),
}

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

    if cvars['prefer_model_over_color'].get_bool():
        make_model_request(
            player, SKIN_PRIORITY, 'rebels', cvars['rebel_model'].get_string())

    else:
        cval = cvars['rebel_color'].get_string().split(',')
        try:
            rgba = tuple(map(int, cval))
        except ValueError:
            rgba = 0, 0, 0

        rgba = (rgba + (255, ))[:4]
        make_color_request(player, SKIN_PRIORITY, 'rebels', rgba)

    # TODO: flash
    # TODO: sound

    InternalEvent.fire('jail_rebel_set', player=player)


def _unset_rebel(player):
    _rebels.discard(player)

    cancel_color_request(player, 'rebels')
    cancel_model_request(player, 'rebels')

    InternalEvent.fire('jail_rebel_unset', player=player)


def _can_rebel(player):
    # 1. Check if we're enabled
    if not cvars['enabled'].get_bool():
        return False

    # 2. If round is over, they can't rebel
    if round_end:
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
    if _can_rebel(player) and not player.isdead:
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


def register_rebel_filter(filter_):
    """ Register new rebel filter. """
    if filter_ in _filters:
        raise ValueError("Filter '%s' is already registered" % filter_)
    _filters.append(filter_)


def unregister_rebel_filter(filter_):
    """ Unregister given rebel filter. """
    _filters.remove(filter_)


@Event('player_death_real')
def on_player_death_real(game_event):
    player = main_player_manager[game_event.get_int('userid')]

    if player not in _rebels:
        return

    _unset_rebel(player)

    aid = game_event.get_int('attacker')
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
    player = main_player_manager[game_event.get_int('userid')]

    # Only able rebel against guards
    if player.team != GUARDS_TEAM:
        return

    # They don't rebel if, say, flashbang was used
    # TODO: Save this cvar on change, don't require it every time
    if (game_event.get_string('weapon') in
            cvars['soft_weapons'].get_string().split(',')):

        return

    aid = game_event.get_int('attacker')
    # World- and self-damage won't count
    if aid == player.userid or not aid:
        return

    attacker = main_player_manager[aid]
    # Further checks on attacker
    if not _can_rebel(attacker):
        return

    if attacker.isdead:
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
        # TODO: Save this cvar on change, don't require it every time
        forbidden_weapons = cvars['forbidden_weapons'].get_string().split(',')
        should_rebel = weapon_class[7:] in forbidden_weapons

        if IGNORE_MAP_REBELWEAPONS:
            return should_rebel
        # ArcJail allows mapmakers to say if a picked weapon:
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

    player = main_player_manager[game_event.get_int('userid')]
    if player.isdead or not _can_rebel(player):
        return

    weapon_class = 'weapon_%s' % game_event.get_string('item')

    for entity in EntityIter(weapon_class):
        try:
            owner_index = index_from_inthandle(entity.owner)
        except (OverflowError, ValueError):
            continue

        if owner_index == player.index:
            break

    else:
        return

    if does_weapon_trigger_rebel(player, weapon_class, entity):
        if entity.index in _hot_weapons:
            player.client_command("use {0};".format(weapon_class), True)
            player.client_command("drop;", True)
        else:
            _set_rebel(player)
            broadcast(strings_module['by_pickup'].tokenize(rebel=player.name))


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    _rebels.discard(event_var['player'])


@Event('round_start')
def on_round_start(game_event):
    reset_rebels()

    global round_end
    round_end = False


@Event('round_end')
def on_round_end(game_event):
    global round_end
    round_end = True


@InternalEvent('load')
def on_load(event_var):
    is_rebel = lambda player: main_player_manager[player.userid] in _rebels
    PlayerIter.register_filter('jail_rebel', is_rebel)


@InternalEvent('unload')
def on_unload(event_var):
    PlayerIter.unregister_filter('jail_rebel')


@ClientCommand('drop')
def cmd_on_drop(command, index):
    # TODO: Save this cvar on change, don't require it every time
    # We're in client command callback, they can DoS by spamming this command
    if not cvars['drop_hot_weapons'].get_bool():
        return

    player = main_player_manager.get_by_index(index)
    if not (player.team == GUARDS_TEAM or is_rebel(player)):
        return True

    weapons = []
    for entity in EntityIter():
        if not entity.classname.startswith('weapon_'):
            continue

        try:
            owner_index = index_from_inthandle(entity.owner)
        except (OverflowError, ValueError):
            continue

        if owner_index == player.index:
            weapons.append(entity)

    def confirm_weapon_drop():
        for entity in weapons:
            try:
                owner_index = index_from_inthandle(entity.owner)
            except (OverflowError, ValueError):
                pass
            else:
                if owner_index == player.index:
                    continue

            if entity.index in _hot_weapons:
                _hot_weapons[entity.index].cancel()

            def cool_weapon(entity=entity):
                _hot_weapons.pop(entity.index, None)

            _hot_weapons[entity.index] = Delay(HOT_WEAPON_TIMEOUT, cool_weapon)

    Delay(0, confirm_weapon_drop)

    return True
