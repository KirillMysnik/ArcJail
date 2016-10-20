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

from random import randint

from players.constants import HitGroup
from events import event_manager
from memory import make_object
from weapons.entity import Weapon

from controlled_cvars.handlers import int_handler

from ....resource.strings import build_module_strings

from ...damage_hook import protected_player_manager

from ...equipment_switcher import (
    register_weapon_drop_filter, register_weapon_pickup_filter,
    saved_player_manager, unregister_weapon_drop_filter,
    unregister_weapon_pickup_filter)

from ...jail_map import get_lrs

from ...players import main_player_manager

from ... import build_module_config

from .. import add_available_game, HiddenSetting, stage

from ..base_classes.combat_game import CombatGame


strings_module = build_module_strings('lrs/russian_roulette')
config_manager = build_module_config('lrs/russian_roulette')

config_manager.controlled_cvar(
    int_handler,
    "fatal_shot_number_min",
    default=1,
    description="Minimum number of the shot that can become fatal"
)
config_manager.controlled_cvar(
    int_handler,
    "fatal_shot_number_max",
    default=15,
    description="Maximum number of the shot that can become fatal"
)


class RussianRoulette(CombatGame):
    _caption = strings_module['title']
    module = "russian_roulette"
    settings = [
        HiddenSetting('health', 1),
        HiddenSetting('using_map_data', True),
        HiddenSetting('weapons', ('weapon_deagle', )),
    ]

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._killing_loser = False
        self._shots_fired = 0
        self._fatal_shot_number = randint(
            config_manager['fatal_shot_number_min'],
            config_manager['fatal_shot_number_max'],
        )

    @stage('combatgame-entry')
    def stage_combatgame_entry(self):
        for player in self._players:
            player.stuck = True

        event_manager.register_for_event('weapon_fire', self._on_weapon_fire)

    @stage('undo-combatgame-entry')
    def stage_undo_combatgame_entry(self):
        for player in self._players:
            player.stuck = False

        event_manager.unregister_for_event('weapon_fire', self._on_weapon_fire)

    @stage('mapgame-equip-weapons')
    def stage_mapgame_equip_weapons(self):
        weapon_classname = self._settings['weapons'][0]

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]
            equipment_player.save_weapons()

            equipment_player.infinite_weapons.clear()

        weapon = make_object(
            Weapon, self.guard.give_named_item(weapon_classname))
        weapon.clip = 0
        weapon.ammo = 0

        weapon = make_object(
            Weapon, self.prisoner.give_named_item(weapon_classname))
        weapon.clip = 1
        weapon.ammo = 0

        register_weapon_drop_filter(self._weapon_drop_filter)
        register_weapon_pickup_filter(self._weapon_pickup_filter)

    @stage('undo-mapgame-equip-weapons')
    def stage_undo_mapgame_equip_weapons(self):
        unregister_weapon_drop_filter(self._weapon_drop_filter)
        unregister_weapon_pickup_filter(self._weapon_pickup_filter)

        for player in self._players:
            equipment_player = saved_player_manager[player.index]
            equipment_player.restore_weapons()

    @stage('equip-damage-hooks')
    def stage_equip_damage_hooks(self):
        for player, opponent in (self._players, reversed(self._players)):
            def hook_hurt(counter, info, player=player, opponent=opponent):
                if self._killing_loser and info.attacker == opponent.index:
                    return True

                return False

            p_player = protected_player_manager[player.index]

            counter = self._counters[player.index] = p_player.new_counter()
            counter.health = self._settings.get('health', 100)
            counter.hook_hurt = hook_hurt

            p_player.set_protected()

    def _on_weapon_fire(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if player not in self._players:
            return

        opponent = self.prisoner if player == self.guard else self.guard

        self._shots_fired += 1
        if self._shots_fired >= self._fatal_shot_number:
            self._killing_loser = True

            player.take_damage(
                self._settings['health'] + 1,
                attacker_index=opponent.index,
                hitgroup=HitGroup.HEAD
            )

        else:
            for weapon in opponent.weapons():
                if weapon.classname == self._settings['weapons'][0]:
                    weapon.clip = 1
                    break

    @classmethod
    def get_available_launchers(cls):
        if get_lrs(cls.module):
            return (cls.GameLauncher(cls), )
        return ()

add_available_game(RussianRoulette)
