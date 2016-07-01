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

from entities.constants import WORLD_ENTITY_INDEX
from entities.entity import Entity
from entities.helpers import index_from_pointer
from entities.hooks import EntityCondition, EntityPreHook
from entities import TakeDamageInfo
from listeners.tick import Delay
from memory import make_object
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
    default=100,
    description="Amount of health used to protect players against damage",
)


KEYHINT_REFRESH_INTERVAL = 1
FINISHING_DAMAGE = 1000
HIDEHUD_PROP = 'm_Local.m_iHideHUD'


def is_world(index):
    if index == WORLD_ENTITY_INDEX:
        return True

    if Entity(index).classname != 'player':
        return True

    return False


def get_hook(flags, next_hook=(lambda counter, info: True)):
    # Hooks: S = self, W = world, P = prisoners, G = guards
    flags = flags.upper()

    def hook(counter, info):
        if 'S' in flags:
            if counter.owner.player.index == info.attacker:
                return next_hook(counter, info)

        if 'W' in flags:
            if is_world(info.attacker):
                return next_hook(counter, info)

        if (info.attacker != counter.owner.player.index and
                not is_world(info.attacker)):

            attacker = main_player_manager[info.attacker]
            if 'P' in flags:
                if attacker.team == PRISONERS_TEAM:
                    return next_hook(counter, info)

            if 'G' in flags:
                if attacker.team == GUARDS_TEAM:
                    return next_hook(counter, info)

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

            self.hook_hurt = lambda health_counter, info: True
            self.hook_death = lambda health_counter, info: True

        def _hurt(self, info):
            if not self.hook_hurt(self, info):
                return True

            self.health -= info.damage
            if self.health <= 0:
                if (self.hook_death(self, info) and
                        not self.owner.dead):

                    self.owner._show_health(hide=True)
                    self.owner.dead = True

                    info.damage = FINISHING_DAMAGE

            else:
                self.owner._show_health()

                info.damage = 0

            return None

        def delete(self):
            self.owner.delete_counter(self)

        def format_display(self):
            if not self.display:
                return None

            return self.display.tokenize(
                amount=int(self.health) if self.health > 0 else '∞')

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

    def _hurt(self, info):
        if self._pre_protection_health is None:
            return

        rs = []
        for counter in self._counters:
            rs.append(counter._hurt(info))

        if any(rs) and not self.dead:
            return True

        return None

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


@EntityPreHook(EntityCondition.is_player, 'on_take_damage')
def on_take_damage(args):
    protected_player = protected_player_manager[index_from_pointer(args[0])]
    if protected_player.dead:
        return

    info = make_object(TakeDamageInfo, args[1])
    return protected_player._hurt(info)


@InternalEvent('player_respawn')
def on_player_respawn(event_var):
    player = event_var['player']
    protected_player = protected_player_manager[player.index]
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
