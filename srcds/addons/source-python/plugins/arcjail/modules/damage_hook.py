from entities.helpers import index_from_inthandle
from events import Event
from filters.entities import EntityIter
from listeners.tick import Delay
from messages import KeyHintText
from players.constants import HideHudFlags
from players.helpers import get_client_language

from controlled_cvars.handlers import int_handler

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager

from ..resource.strings import build_module_strings

from .players import main_player_manager

from .teams import GUARDS_TEAM, PRISONERS_TEAM

from . import build_module_config


strings_module = build_module_strings('damage_hook')
config_manager = build_module_config('damage_hook')

config_manager.controlled_cvar(
    int_handler,
    "protection_hp",
    default=1000,
    description="Amount of health used to protect players against damage",
)


KEYHINT_REFRESH_INTERVAL = 1
FINISHING_DAMAGE = 100
HIDEHUD_PROP = 'm_Local.m_iHideHUD'


def get_hook(flags, next_hook=(lambda counter, game_event: True)):
    # Hooks: S = self, W = world, P = prisoners, G = guards
    flags = flags.upper()

    def hook(counter, game_event):
        userid = game_event.get_int('userid')
        aid = game_event.get_int('attacker')

        if 'S' in flags:
            if userid == aid:
                return next_hook(counter, game_event)

        if 'W' in flags:
            if not aid:
                return next_hook(counter, game_event)

        if userid != aid and aid:
            attacker = main_player_manager[aid]
            if 'P' in flags:
                if attacker.team == PRISONERS_TEAM:
                    return next_hook(counter, game_event)

            if 'G' in flags:
                if attacker.team == GUARDS_TEAM:
                    return next_hook(counter, game_event)

        return False

    return hook


class ProtectedPlayer:
    class HealthCounter:
        def __init__(self, owner, health, display):
            self.owner = owner
            self.display = display
            if health is None:
                self.health = owner.player.health
            else:
                self.health = health

            self.hook_hurt = lambda health_counter, game_event: True
            self.hook_death = lambda health_counter, game_event: True
            self.death_callback = lambda: None

        def _hurt(self, game_event):
            player = self.owner.player
            if not self.hook_hurt(self, game_event):
                return

            self.health -= game_event.get_int('dmg_health')
            if self.health <= 0:
                if (self.hook_death(self, game_event) and
                        not self.owner.dead):

                    self.owner._show_health(hide=True)
                    self.owner.dead = True

                    player.health = 0

                    aid = game_event.get_int('attacker')
                    if aid != 0:
                        attacker = main_player_manager[aid]

                        for weapon in EntityIter("weapon_{0}".format(
                                game_event.get_string('item'))):

                            if weapon.owner == -1:
                                continue
                            if (index_from_inthandle(weapon.owner) ==
                                    attacker.index):

                                weapon_index = weapon.index
                                break
                        else:
                            weapon_index = None

                        player.take_damage(
                            FINISHING_DAMAGE,
                            attacker_index=attacker.index,
                            weapon_index=weapon_index
                        )

                    else:
                        player.take_damage(FINISHING_DAMAGE)

                    self.death_callback()

            else:
                self.owner._show_health()

        def delete(self):
            self.owner.delete_counter(self)

        def format_display(self):
            if not self.display:
                return None

            return self.display.tokenize(
                amount=self.health if self.health > 0 else '∞')

    def __init__(self, player):
        self.player = player
        self._counters = []
        self._pre_protection_health = None
        self._language = get_client_language(player.index)
        self.dead = player.dead

    def set_protected(self):
        if self._pre_protection_health is not None:
            return

        if self.dead:
            return

        self._pre_protection_health = self.player.health
        self.player.health = config_manager['protection_hp']

        hidehud = self.player.get_property_int(
            HIDEHUD_PROP) | HideHudFlags.HEALTH

        self.player.set_property_int(HIDEHUD_PROP, hidehud)

    def unset_protected(self):
        if self._pre_protection_health is None:
            return

        if self.dead:
            return

        self.player.health = self._pre_protection_health
        self._pre_protection_health = None

        hidehud = self.player.get_property_int(
            HIDEHUD_PROP) & ~HideHudFlags.HEALTH

        self.player.set_property_int(HIDEHUD_PROP, hidehud)

    def new_counter(self, health=None, display=False):
        counter = self.HealthCounter(self, health, display)
        self._counters.append(counter)
        return counter

    def delete_counter(self, counter):
        if counter not in self._counters:
            return

        self._counters.remove(counter)
        if not self._counters:
            self._show_health(hide=True)

    def _hurt(self, game_event):
        if self._pre_protection_health is None:
            return

        self.player.health = config_manager['protection_hp']

        for counter in self._counters:
            counter._hurt(game_event)

    def _spawn(self, game_event):
        self._pre_protection_health = None
        self.dead = False
        self._counters = []

    def _show_health(self, hide=False):
        if hide:
            KeyHintText("").send(self.player.index)
            return

        content = []
        for counter in self._counters:
            counter_str = counter.format_display()
            if counter_str is not None:
                content.append(counter_str.get_string(self._language))

        if not content:
            return

        KeyHintText('\n'.join(content)).send(self.player.index)


protected_player_manager = BasePlayerManager(ProtectedPlayer)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    protected_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    protected_player_manager.delete(player)


@Event('player_hurt')
def on_player_hurt(game_event):
    protected_player = protected_player_manager[game_event.get_int('userid')]
    if protected_player.dead:
        return

    protected_player._hurt(game_event)


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    protected_player = protected_player_manager[player.userid]
    protected_player._spawn(event_var['game_event'])


delay = None


@InternalEvent('load')
def on_load(event_var):
    def callback():
        for protected_player in protected_player_manager.values():
            if not protected_player.dead:
                protected_player._show_health()

        global delay
        delay = Delay(KEYHINT_REFRESH_INTERVAL, callback)

    callback()


@InternalEvent('unload')
def on_unload(event_var):
    if delay:
        delay.cancel()
