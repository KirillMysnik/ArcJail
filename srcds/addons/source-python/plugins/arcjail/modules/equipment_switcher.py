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
from entities.entity import Entity
from entities.helpers import edict_from_index, index_from_pointer
from entities.hooks import EntityCondition, EntityPreHook
from listeners import OnEntitySpawned
from listeners.tick import Delay
from memory import make_object
from mathlib import NULL_VECTOR
from weapons.entity import Weapon
from weapons.manager import weapon_manager

from ..arcjail import InternalEvent

from ..common import give_named_item

from ..classes.base_player_manager import BasePlayerManager

from ..resource.memory import CCSPlayer

from .players import main_player_manager


INFINITE_AMMO_REFILL_INTERVAL = 5
PROJECTILE_REFILL_DELAY = 1.5
PROJECTILE_MAPPING = {
    'hegrenade_projectile': 'weapon_hegrenade',
    'smokegrenade_projectile': 'weapon_smokegrenade',
    'flashbang_projectile': 'weapon_flashbang',
    # TODO: Add CS:GO grenades and export all these to a file
}
PROJECTILE_CLASSNAMES = PROJECTILE_MAPPING.values()


class SavedPlayer:
    def __init__(self, player):
        self._ammo_refill_delay = None
        self._nade_refill_delay = None
        self.player = player
        self.health = 0
        self.saved_weapons = []
        self.infinite_weapons = []

    def _nade_thrown(self, weapon_classname):
        if self._ammo_refill_delay is None:
            return

        if weapon_classname not in self.infinite_weapons:
            return

        self._nade_refill_delay = Delay(
            PROJECTILE_REFILL_DELAY,
            give_named_item,
            self.player, weapon_classname, 0
        )

    def save_health(self):
        self.health = self.player.health

    def save_weapons(self):
        self.saved_weapons = []

        for weapon in self.player.weapons():
            weapon_dict = {
                'classname': weapon.classname,
                'subtype': weapon.get_property_int('m_iSubType'),
                'ammo': weapon.ammo if weapon.has_ammo() else None,
                'clip': weapon.ammo if weapon.has_clip() else None
            }

            self.saved_weapons.append(weapon_dict)

        self.strip()

    def save_all(self):
        self.save_health()
        self.save_weapons()

    def strip(self):
        for weapon in self.player.weapons():
            self.player.drop_weapon(weapon.pointer, NULL_VECTOR, NULL_VECTOR)
            weapon.remove()

    def restore_health(self):
        self.player.health = self.health

    def restore_weapons(self):
        self.strip()
        for weapon_dict in self.saved_weapons:
            weapon = Weapon.create(weapon_dict['classname'])
            weapon.teleport(self.player.origin, None, None)
            weapon.spawn()

            if weapon_dict['clip'] is not None:
                weapon.clip = weapon_dict['clip']

            if weapon_dict['ammo'] is not None:
                weapon.ammo = weapon_dict['ammo']

    def restore_all(self):
        self.restore_health()
        self.restore_weapons()

    def max_ammo(self, weapon_classnames):
        maxed_weapons = []

        for weapon in self.player.weapons():
            if weapon.classname not in weapon_classnames:
                continue

            if weapon.classname in PROJECTILE_CLASSNAMES:
                continue

            weapon_class = weapon_manager[weapon.classname]
            if not weapon.has_ammo() or weapon_class.maxammo <= 0:
                continue

            weapon.ammo = weapon_class.maxammo
            maxed_weapons.append(weapon)

        return maxed_weapons

    def _refill_infinite_ammo(self):
        self.max_ammo(self.infinite_weapons)

        self._ammo_refill_delay = Delay(
            INFINITE_AMMO_REFILL_INTERVAL, self._refill_infinite_ammo)

    def infinite_on(self):
        if (self._ammo_refill_delay is not None or
                self._nade_refill_delay is not None):

            raise ValueError("Infinite equipment is already turned on")

        maxed_weapon_classnames = map(
            lambda weapon: weapon.classname,
            self.max_ammo(self.infinite_weapons)
        )

        self.infinite_weapons = list(filter(
            lambda classname:
                classname in maxed_weapon_classnames or
                classname in PROJECTILE_CLASSNAMES,
            self.infinite_weapons
        ))

        self._ammo_refill_delay = Delay(
            INFINITE_AMMO_REFILL_INTERVAL, self._refill_infinite_ammo)

    def infinite_off(self):
        if self._ammo_refill_delay is None:
            raise ValueError("Infinite equipment is already turned off")

        self._ammo_refill_delay.cancel()
        self._ammo_refill_delay = None

        if self._nade_refill_delay is not None:
            if self._nade_refill_delay.running:
                self._nade_refill_delay.cancel()

            self._nade_refill_delay = None

saved_player_manager = BasePlayerManager(SavedPlayer)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    saved_player_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    saved_player_manager.delete(player)


@OnEntitySpawned
def listener_on_entity_spawned(base_entity):
    if base_entity.classname not in PROJECTILE_MAPPING:
        return

    entity = Entity(base_entity.index)
    owner = entity.owner
    if owner is None:
        return

    saved_player = saved_player_manager[owner.index]
    weapon_classname = PROJECTILE_MAPPING[base_entity.classname]
    saved_player._nade_thrown(weapon_classname)


bump_weapon_function = None
weapon_pickup_filters = []
weapon_drop_filters = []


def pre_bump_weapon(pointers):
    pointer_player, pointer_weapon = pointers
    player = main_player_manager[index_from_pointer(pointer_player)]

    weapon_index = index_from_pointer(pointer_weapon)

    for callback in weapon_pickup_filters:
        if callback(player, weapon_index) is False:
            # Disallow pick-up
            return True

    # Allow pick-up
    return None


def check_bump_weapons():
    global bump_weapon_function
    if weapon_pickup_filters and bump_weapon_function is None:
        for player in main_player_manager.values():
            break

        else:
            raise RuntimeError("No players found, can't hook bump_weapon")

        bump_weapon_function = player.bump_weapon
        bump_weapon_function.add_pre_hook(pre_bump_weapon)

    elif not weapon_pickup_filters and bump_weapon_function is not None:
        bump_weapon_function.remove_pre_hook(pre_bump_weapon)
        bump_weapon_function = None


def register_weapon_pickup_filter(callback):
    if callback in weapon_pickup_filters:
        raise ValueError("Filter already registered")

    weapon_pickup_filters.append(callback)
    check_bump_weapons()


def unregister_weapon_pickup_filter(callback):
    if callback not in weapon_pickup_filters:
        raise ValueError("Filter not registered")

    weapon_pickup_filters.remove(callback)
    check_bump_weapons()


@ClientCommand('drop')
def cl_drop(command, index):
    player = main_player_manager[index]

    for callback in weapon_drop_filters:
        if callback(player) is False:
            # Disallow drop
            return False

    # Allow drop
    return True


def register_weapon_drop_filter(callback):
    if callback in weapon_drop_filters:
        raise ValueError("Filter already registered")

    weapon_drop_filters.append(callback)


def unregister_weapon_drop_filter(callback):
    if callback not in weapon_drop_filters:
        raise ValueError("Filter not registered")

    weapon_drop_filters.remove(callback)


@InternalEvent('unload')
def on_unload(event_var):
    if bump_weapon_function is not None:
        bump_weapon_function.remove_pre_hook(pre_bump_weapon)


def make_weapon_can_use(player):
    return make_object(CCSPlayer, player.pointer).weapon_can_use


@EntityPreHook(EntityCondition.is_player, make_weapon_can_use)
def pre_weapon_can_use(args):
    """A little fix for picking up knives in CS:GO."""
    return True
