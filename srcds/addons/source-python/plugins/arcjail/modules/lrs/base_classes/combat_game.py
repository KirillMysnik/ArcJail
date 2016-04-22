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

from contextlib import suppress
from random import shuffle

from entities.helpers import edict_from_index

from ...damage_hook import (
    protected_player_manager, strings_module as strings_damage_hook)

from ...equipment_switcher import (
    register_weapon_drop_filter, register_weapon_pickup_filter,
    saved_player_manager, unregister_weapon_drop_filter,
    unregister_weapon_pickup_filter)

from ...falldmg_protector import unprotect

from ...games import play_flawless_effects

from ...jail_map import get_lrs, teleport_player

from ...players import main_player_manager

from ...show_damage import show_damage

from .. import config_manager, game_event_handler, stage

from .prepare_time import PrepareTime


class CombatGame(PrepareTime):
    stage_groups = {
        'destroy': [
            "prepare-cancel-delays",
            "unsend-popups",
            "destroy",
        ],
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
        'mapgame-start': [
            "mapgame-equip-weapons",
            "equip-damage-hooks",
            "mapgame-fire-mapdata-outputs",
            "mapgame-entry",
            "combatgame-entry",
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self.map_data = None
        if self._settings.get('using_map_data', True):
            lrs = get_lrs(self.module)
            if lrs:
                self.map_data = lrs[0]

        self._flawless = {
            self.prisoner.userid: True,
            self.guard.userid: True,
        }
        self._counters = {}
        self._delays = []

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self.set_stage_group('mapgame-start')

    @stage('combatgame-entry')
    def stage_combatgame_entry(self):
        pass

    @stage('prepare-entry')
    def stage_prepare_entry(self):
        self.insert_stage_group('mapgame-prepare')

    @stage('mapgame-entry')
    def stage_mapgame_entry(self):
        if config_manager['combat_lr_start_sound'] is not None:
            indexes = (self.prisoner.index, self.guard.index)
            config_manager['combat_lr_start_sound'].play(*indexes)

    @stage('mapgame-prepare-entry')
    def stage_mapgame_prepare_entry(self):
        pass

    @stage('mapgame-cancel-falldmg-protection')
    def stage_mapgame_cancel_falldmg_protection(self):
        """Cancel any falldmg protections previous games might have set."""
        for player in self._players:
            with suppress(ValueError):
                unprotect(player)

    @stage('mapgame-fire-mapdata-prepare-outputs')
    def stage_mapgame_fire_mapdata_prepare_outputs(self):
        """Fire OnPrepare output on controller entity."""
        if self.map_data is not None:
            self.map_data.prepare()

    @stage('mapgame-fire-mapdata-outputs')
    def stage_mapgame_fire_mapdata_outputs(self):
        """Fire OnStart output on controller entity."""
        if self.map_data is not None:
            self.map_data.start()

    @stage('undo-mapgame-fire-mapdata-outputs')
    def stage_undo_mapgame_fire_mapdata_outputs(self):
        """Fire OnEnd output on controller entity."""
        if self.map_data is not None:
            self.map_data.end()

    @stage('mapgame-teleport-players')
    def stage_mapgame_teleport_players(self):
        """Teleport players and game leader."""
        if self.map_data is None:
            return

        spawnpoints = list(self.map_data.spawnpoints)
        shuffle(spawnpoints)

        for player in self._players:
            teleport_player(player, spawnpoints.pop())

    @stage('mapgame-equip-weapons')
    def stage_mapgame_equip_weapons(self):
        """Equip players with weapons."""
        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]
            equipment_player.save_weapons()

            equipment_player.infinite_weapons.clear()
            for weapon_classname in self._settings.get('weapons', ()):
                player.give_named_item(weapon_classname, 0)
                equipment_player.infinite_weapons.append(weapon_classname)

            equipment_player.infinite_on()

        register_weapon_drop_filter(self._weapon_drop_filter)
        register_weapon_pickup_filter(self._weapon_pickup_filter)

    @stage('undo-mapgame-equip-weapons')
    def stage_undo_mapgame_equip_weapons(self):
        """Restore player's original equipment."""
        unregister_weapon_drop_filter(self._weapon_drop_filter)

        # Important: unregister weapon pickup filter BEFORE
        # restoring player's weapons!
        unregister_weapon_pickup_filter(self._weapon_pickup_filter)

        for player in self._players_all:
            equipment_player = saved_player_manager[player.index]

            if player in self._players:
                equipment_player.restore_weapons()

            equipment_player.infinite_off()

    @stage('equip-damage-hooks')
    def stage_equip_damage_hooks(self):
        def hook_hurt_for_prisoner(counter, info):
            if info.attacker != self.guard.index:
                return False

            self._flawless[self.prisoner.userid] = False

            show_damage(self.guard, info.damage)

            return True

        def hook_death_for_prisoner(counter, game_event):
            saved_player = saved_player_manager[self.prisoner.index]
            saved_player.strip()
            return True

        def hook_hurt_for_guard(counter, info):
            if info.attacker != self.prisoner.index:
                return False

            self._flawless[self.guard.userid] = False

            show_damage(self.prisoner, info.damage)

            return True

        def hook_death_for_guard(counter, game_event):
            saved_player = saved_player_manager[self.guard.index]
            saved_player.strip()
            return True

        for hook_hurt, hook_death, player in zip(
                (hook_hurt_for_prisoner, hook_hurt_for_guard),
                (hook_death_for_prisoner, hook_death_for_guard),
                self._players
        ):

            p_player = protected_player_manager[player.index]

            counter = self._counters[player.userid] = p_player.new_counter(
                display=strings_damage_hook['health game'])

            counter.health = self._settings.get('health', 100)
            counter.hook_hurt = hook_hurt
            counter.hook_death = hook_death

            p_player.set_protected()

    @stage('undo-equip-damage-hooks')
    def stage_undo_survival_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.userid])
            p_player.unset_protected()

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if player not in self._players:
            return

        if player == self.prisoner:
            winner, loser = self.guard, self.prisoner
        else:
            winner, loser = self.prisoner, self.guard

        if self._flawless[winner.userid]:
            play_flawless_effects(self._players)
        
        self._results['winner'] = winner
        self._results['loser'] = loser

        self._players.remove(player)

        self.set_stage_group('win')

    def _weapon_drop_filter(self, player):
        return player not in self._players

    def _weapon_pickup_filter(self, player, weapon_index):
        if player not in self._players:
            return True

        weapon_classname = edict_from_index(weapon_index).classname
        return weapon_classname in self._settings.get('weapons', ())
