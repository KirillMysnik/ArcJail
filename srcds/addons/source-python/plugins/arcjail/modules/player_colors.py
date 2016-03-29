from colors import Color
from events import Event

from ..arcjail import InternalEvent


DEFAULT_COLOR = Color(255, 255, 255)


class PlayerColorRequest:
    def __init__(self, id_, priority, color):
        self.id = id_
        self.priority = priority
        self.color = color

requests = {}


@Event('round_start')
def on_round_start(game_event):
    requests.clear()


@Event('player_death_real')
def on_player_death_real(game_event):
    userid = game_event.get_int('userid')
    if userid in requests:
        del requests[userid]


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    userid = event_var['main_player'].userid
    if userid in requests:
        del requests[userid]


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    if player.userid in requests:
        del requests[player.userid]
    _update_player(player)


def _update_player(player):
    if player.dead:
        return

    if player.userid not in requests:
        player.color = DEFAULT_COLOR
        return

    request_max = None
    for request in requests[player.userid]:
        if request_max is None or request.priority >= request_max.priority:
            request_max = request

    if request_max:
        player.color = request_max.color
    else:
        player.color = DEFAULT_COLOR


def make_color_request(player, priority, id_, color):
    if player.userid not in requests:
        requests[player.userid] = []

    for request in requests[player.userid]:
        if request.id == id_:
            requests[player.userid].remove(request)
            break

    requests[player.userid].append(PlayerColorRequest(id_, priority, color))
    _update_player(player)


def cancel_color_request(player, id_):
    if player.userid not in requests:
        return

    for request in requests[player.userid]:
        if request.id == id_:
            requests[player.userid].remove(request)
            break

    if not requests[player.userid]:
        del requests[player.userid]

    _update_player(player)
