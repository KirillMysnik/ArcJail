from warnings import warn

from engines.precache import Model
from events import Event

from controlled_cvars.handlers import bool_handler, string_handler

from ..arcjail import InternalEvent, load_downloadables

from ..resource.paths import ARCJAIL_CFG_PATH

from .teams import GUARDS_TEAM, PRISONERS_TEAM

from . import build_module_config


DEFAULT_SKIN_PRIORITY = 1


_downloadables = load_downloadables('skins.res')

_precache = {}
with open(ARCJAIL_CFG_PATH / "other" / "skins-precache.res") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        _precache[line] = Model(line)


config_manager = build_module_config('rebels')


config_manager.controlled_cvar(
    bool_handler,
    name="enable_prisoner_model",
    default=1,
    description="Enable/Disable custom prisoner model",
)
config_manager.controlled_cvar(
    string_handler,
    name="prisoner_model",
    default="models/player/arcjail/regular/regular.mdl",
    description="Prisoner model",
)
config_manager.controlled_cvar(
    bool_handler,
    name="enable_guard_model",
    default=0,
    description="Enable/Disable custom guard model",
)
config_manager.controlled_cvar(
    string_handler,
    name="guard_model",
    default="",
    description="Guard model",
)


class UnprecachedModel(Warning):
    pass


class PlayerModelRequest:
    def __init__(self, id_, priority, model):
        self.id = id_
        self.priority = priority
        self.model = model

_requests = {}


def _update_player(player):
    if player.dead:
        return

    if player.userid not in _requests:
        return

    request_max = None
    for request in _requests[player.userid]:
        if request_max is None or request.priority >= request_max.priority:
            request_max = request

    if request_max:
        player.model_index = _precache[request_max.model].index


def make_model_request(player, priority, id_, path):
    if path in _precache:
       player.model_index = _precache[path].index

    else:
        warn(UnprecachedModel("Can't set unprecached model "
                              "'{0}'".format(path)))
        return

    if player.userid not in _requests:
        _requests[player.userid] = []

    for request in _requests[player.userid]:
        if request.id == id_:
            _requests[player.userid].remove(request)
            break

    _requests[player.userid].append(PlayerModelRequest(id_, priority, path))
    _update_player(player)


def cancel_model_request(player, id_):
    if player.userid not in _requests:
        return

    for request in _requests[player.userid]:
        if request.id == id_:
            _requests[player.userid].remove(request)
            break

    if not _requests[player.userid]:
        del _requests[player.userid]

    _update_player(player)


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    if player.userid in _requests:
        _requests[player.userid].clear()

    if player.team == PRISONERS_TEAM:
        if config_manager['enable_prisoner_model']:
            make_model_request(
                player,
                DEFAULT_SKIN_PRIORITY,
                'default-skin',
                config_manager['prisoner_model'],
            )

    elif player.team == GUARDS_TEAM:
        if config_manager['enable_guard_model']:
            make_model_request(
                player,
                DEFAULT_SKIN_PRIORITY,
                'default-skin',
                config_manager['guard_model'],
            )

    _update_player(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    if player.userid in _requests:
        del _requests[player.userid]


@Event('player_death_real')
def on_player_death_real(game_event):
    userid = game_event.get_int('userid')
    if userid in _requests:
        del _requests[userid]
