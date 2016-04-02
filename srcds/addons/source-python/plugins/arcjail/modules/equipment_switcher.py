from commands.client import ClientCommand
from entities.entity import Entity
from entities.helpers import edict_from_index
from entities.helpers import index_from_pointer
from listeners import OnEntitySpawned
from listeners.tick import Delay
from players.helpers import userid_from_inthandle
from weapons.manager import weapon_manager

from mathlib import NULL_VECTOR

from ..arcjail import InternalEvent

from ..classes.base_player_manager import BasePlayerManager

from .players import main_player_manager


INFINITE_AMMO_REFILL_INTERVAL = 5
PROJECTILE_REFILL_DELAY = 1
PROJECTILE_MAPPING = {
    'hegrenade_projectile': 'weapon_hegrenade',
    'smokegrenade_projectile': 'weapon_smokegrenade',
    'flashbang_projectile': 'weapon_flashbang',
    # TODO: Add CS:GO grenades and export all these to a file
}


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
            self.player.give_named_item,
            weapon_classname, 0)

    def save_health(self):
        self.health = self.player.health

    def save_weapons(self):
        self.saved_weapons = []

        for index in self.player.weapon_indexes():
            weapon = Entity(index)
            weapon_dict = {
                'classname': weapon.classname,
                'clip': None,
                'ammo': None,
                'subtype': None,
            }
            if weapon.ammoprop > -1:
                weapon_dict['ammo'] = self.player.get_ammo(weapon.classname)

            weapon_dict['clip'] = weapon.clip
            weapon_dict['subtype'] = weapon.get_property_int('m_iSubType')
            self.saved_weapons.append(weapon_dict)

        self.strip()

    def save_all(self):
        self.save_health()
        self.save_weapons()

    def strip(self):
        for index in self.player.weapon_indexes():
            weapon = Entity(index)
            self.player.drop_weapon(weapon.pointer, NULL_VECTOR, NULL_VECTOR)
            weapon.remove()

    def restore_health(self):
        self.player.health = self.health

    def restore_weapons(self):
        self.strip()
        for weapon_dict in self.saved_weapons:
            self.player.give_named_item(
                weapon_dict['classname'], weapon_dict['subtype'])

            if weapon_dict['clip'] > -1:
                self.player.set_clip(
                    weapon_dict['classname'], weapon_dict['clip'])

            if weapon_dict['ammo'] is not None:
                self.player.set_ammo(
                    weapon_dict['classname'], weapon_dict['ammo'])

    def restore_all(self):
        self.restore_health()
        self.restore_weapons()

    def max_ammo(self, weapon_classnames):
        for index in self.player.weapon_indexes():
            weapon_classname = edict_from_index(index).get_class_name()
            if weapon_classname not in weapon_classnames:
                continue

            weapon_class = weapon_manager[weapon_classname]
            if weapon_class.maxammo > 0:
                self.player.set_ammo(weapon_classname, weapon_class.maxammo)

    def infinite_on(self):
        if (self._ammo_refill_delay is not None or
                    self._nade_refill_delay is not None):

            raise ValueError("Infinite equipment is already turned on")

        def refill_ammo():
            self.max_ammo(self.infinite_weapons)
            self._ammo_refill_delay = Delay(
                INFINITE_AMMO_REFILL_INTERVAL, refill_ammo)

        refill_ammo()

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
def listener_on_entity_spawned(index, base_entity):
    if base_entity.classname not in PROJECTILE_MAPPING:
        return

    entity = Entity(index)
    if entity.owner == -1:
        return

    saved_player = saved_player_manager[userid_from_inthandle(entity.owner)]
    weapon_classname = PROJECTILE_MAPPING[base_entity.classname]
    saved_player._nade_thrown(weapon_classname)


bump_weapon_function = None
weapon_pickup_filters = []
weapon_drop_filters = []


def pre_bump_weapon(pointers):
    pointer_player, pointer_weapon = pointers
    player = main_player_manager.get_by_index(
        index_from_pointer(pointer_player))

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
    player = main_player_manager.get_by_index(index)

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
