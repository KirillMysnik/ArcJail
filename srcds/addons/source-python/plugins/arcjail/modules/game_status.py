from events import Event

from ..arcjail import InternalEvent


class GameStatus:
    FREE = 1
    BUSY = 2
    NOT_STARTED = 3

    @classmethod
    def is_valid_status(cls, status):
        return status in (cls.FREE, cls.BUSY, cls.NOT_STARTED)


_status = None


def get_status():
    return _status


def set_status(status):
    if not GameStatus.is_valid_status(status):
        raise ValueError("Invalid status: '{0}'".format(status))

    global _status
    if _status == GameStatus.NOT_STARTED and status == GameStatus.FREE:
        InternalEvent.fire('arcjail_game_started')

    _status = status


@Event('round_start')
def on_round_start(game_event):
    global _status
    _status = GameStatus.NOT_STARTED


@InternalEvent('load')
def on_load(event_var):
    global _status
    _status = GameStatus.NOT_STARTED
