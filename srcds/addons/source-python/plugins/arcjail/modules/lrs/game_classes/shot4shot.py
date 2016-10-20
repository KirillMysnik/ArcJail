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

from entities.constants import DamageTypes
from events import event_manager
from listeners.tick import Delay
from memory import make_object
from weapons.entity import Weapon

from ....internal_events import InternalEvent
from ....resource.strings import build_module_strings

from ...damage_hook import (
    protected_player_manager, strings_module as strings_damage_hook)
from ...equipment_switcher import (
    register_weapon_drop_filter, register_weapon_pickup_filter,
    saved_player_manager, unregister_weapon_drop_filter,
    unregister_weapon_pickup_filter)
from ...players import broadcast, player_manager, tell
from ...show_damage import show_damage

from .. import (
    add_available_game, HiddenSetting, Setting, SettingOption,
    stage, strings_module as strings_common)
from ..base_classes.combat_game import CombatGame


BULLET_TRAVEL_TIME = 0.1


strings_module = build_module_strings('lrs/shot4shot')


class Shot4Shot(CombatGame):
    _caption = strings_module['title']
    module = "shot4shot"
    settings = [
        Setting('using_map_data', strings_common['settings map_data'],
                SettingOption(
                    True, strings_common['setting map_data yes'], True),
                SettingOption(False, strings_common['setting map_data no']),
                ),
        Setting('weapons', strings_module['settings weapons'],
                SettingOption(("weapon_glock",), "Glock"),
                SettingOption(("weapon_usp",), "USP"),
                SettingOption(("weapon_p228",), "P-228"),
                SettingOption(("weapon_deagle",), "Desert Eagle", True),
                SettingOption(("weapon_fiveseven",), "Five-Seven"),
                SettingOption(("weapon_elite",), "Elite"),
                ),
        Setting('hs_only', strings_module['settings hs_only'],
                SettingOption(
                    True, strings_module['setting hs_only yes'], True),

                SettingOption(False, strings_module['setting hs_only no']),
                ),
        Setting('competitive', strings_module['settings competitive'],
                SettingOption(
                    True, strings_module['setting competitive yes'], True),

                SettingOption(
                    False, strings_module['setting competitive no']),
                ),
        HiddenSetting('health', 100)
    ]

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._killing_loser = False
        self._shots_fired = 0
        self._score = {
            self.guard.index: 0,
            self.prisoner.index: 0,
        }

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
            if self._settings['competitive']:
                def hook_hurt(counter, info, player=player, opponent=opponent):
                    if self._killing_loser:
                        return True

                    if info.attacker != opponent.index:
                        return False

                    landed = True
                    if self._settings['hs_only']:
                        if not info.type & DamageTypes.HEADSHOT:
                            landed = False

                    if landed:
                        self._flawless[player.index] = False
                        self._score[info.attacker] += 1

                        InternalEvent.fire('jail_stop_accepting_bets',
                                           instance=self)

                        show_damage(opponent, self._settings['health'])

                    return False

            else:
                def hook_hurt(counter, info, player=player, opponent=opponent):
                    if info.attacker != opponent.index:
                        return False

                    if self._settings['hs_only']:
                        if info.type & DamageTypes.HEADSHOT:
                            info.damage = self._settings['health']
                        else:
                            return False

                    self._flawless[player.index] = False

                    InternalEvent.fire('jail_stop_accepting_bets',
                                       instance=self)

                    show_damage(opponent, info.damage)

                    return True

            p_player = protected_player_manager[player.index]

            counter = self._counters[player.index] = p_player.new_counter(
                display=strings_damage_hook['health game'])

            counter.health = self._settings.get('health', 100)
            counter.hook_hurt = hook_hurt

            p_player.set_protected()

    @stage('combatgame-entry')
    def stage_combatgame_entry(self):
        if self._settings['competitive']:
            event_manager.register_for_event(
                'weapon_fire', self._on_weapon_fire_competitive)

        else:
            event_manager.register_for_event(
                'weapon_fire', self._on_weapon_fire_classic)

    @stage('undo-combatgame-entry')
    def stage_undo_combatgame_entry(self):
        if self._settings['competitive']:
            event_manager.unregister_for_event(
                'weapon_fire', self._on_weapon_fire_competitive)

        else:
            event_manager.unregister_for_event(
                'weapon_fire', self._on_weapon_fire_classic)

    def _on_weapon_fire_classic(self, game_event):
        player = player_manager.get_by_userid(game_event['userid'])

        if player not in self._players:
            return

        opponent = self.prisoner if player == self.guard else self.guard
        for weapon in opponent.weapons():
            if weapon.classname == self._settings['weapons'][0]:
                weapon.clip = 1
                break

    def _on_weapon_fire_competitive(self, game_event):
        player = player_manager.get_by_userid(game_event['userid'])

        if player not in self._players:
            return

        opponent = self.prisoner if player == self.guard else self.guard

        self._shots_fired += 1
        self._delays.append(Delay(
            BULLET_TRAVEL_TIME, self._competitive_bullet_hit, opponent))

    def _competitive_bullet_hit(self, opponent):
        score_guard = self._score[self.guard.index]
        score_prisoner = self._score[self.prisoner.index]

        broadcast(strings_module['score'].tokenize(
            player1=self.prisoner.name,
            score1=score_prisoner,
            player2=self.guard.name,
            score2=score_guard,
        ))

        # Check if it's the end of another round
        if self._shots_fired % 2 == 0:
            if score_guard != score_prisoner:
                self._killing_loser = True

                if score_guard > score_prisoner:
                    self.prisoner.take_damage(
                        self._settings['health'],
                        attacker_index=self.guard.index,
                    )
                else:
                    self.guard.take_damage(
                        self._settings['health'],
                        attacker_index=self.prisoner.index,
                    )

                return

            tell(self._players, strings_module['round_draw'])

        for weapon in opponent.weapons():
            if weapon.classname == self._settings['weapons'][0]:
                weapon.clip = 1
                break

add_available_game(Shot4Shot)
