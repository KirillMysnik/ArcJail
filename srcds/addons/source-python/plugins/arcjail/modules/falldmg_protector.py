from events import Event
from listeners.tick import Delay
from messages import Shake

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager

from ..resource.strings import build_module_strings

from .damage_hook import get_hook, protected_player_manager


FALL_PROT_SHAKE_MAGNITUDE = 20
FALL_PROT_SHAKE_TIME = 0.7


strings_module = build_module_strings('falldmg_protector')


class FallProtectedPlayer:
    def __init__(self, player):
        self.player = player
        self.p_player = protected_player_manager[player.index]

        self._delay = None
        self._counter = None

    def protect(self, seconds):
        if self._counter is not None:
            raise ValueError(
                "Player {} already protected".format(self.player.userid)
            )

        self._counter = self.p_player.new_counter(
            health=0, display=strings_module['health falldmg_protection'])

        def sub_hook(counter, info):
            self.p_player.delete_counter(counter)
            self.p_player.unset_protected()

            self._counter = None

            Shake(
                FALL_PROT_SHAKE_MAGNITUDE, FALL_PROT_SHAKE_TIME
            ).send(self.player.index)

            self._delay.cancel()

            return False

        self._counter.hook_hurt = get_hook('W', next_hook=sub_hook)

        def delay_callback():
            self.p_player.delete_counter(self._counter)
            self.p_player.unset_protected()

            self._counter = None

        self._delay = Delay(seconds, delay_callback)
        self.p_player.set_protected()

    def unprotect(self):
        if self._counter is None:
            raise ValueError(
                "Player {} is not protected yet".format(self.player.userid)
            )

        self.cancel_delay()

        self.p_player.delete_counter(self._counter)
        self.p_player.unset_protected()

        self._counter = None

    @property
    def protected(self):
        return self._counter is not None

    def cancel_delay(self):
        if self._delay is not None and self._delay.running:
            self._delay.cancel()


fall_protected_player_manager = BasePlayerManager(FallProtectedPlayer)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    fall_protected_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    fall_protected_player_manager.delete(player)


@Event('player_death_real')
def on_player_death_real(game_event):
    p_player = fall_protected_player_manager.get_by_userid(
        game_event.get_int('userid'))

    p_player.cancel_delay()


@Event('round_start')
def on_round_start(game_event):
    for p_player in fall_protected_player_manager.values():
        p_player.cancel_delay()


def protect(player, map_data):
    if map_data['FALL_DAMAGE_PROTECTION_TIMEOUT'] <= 0:
        return

    fall_protected_player_manager[player.index].protect(
        map_data['FALL_DAMAGE_PROTECTION_TIMEOUT'])


def unprotect(player):
    fall_protected_player_manager[player.index].unprotect()


def is_protected(player):
    return fall_protected_player_manager[player.index].protected
