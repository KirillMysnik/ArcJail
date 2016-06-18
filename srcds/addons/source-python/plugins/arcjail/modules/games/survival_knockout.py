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

from entities.entity import Entity

from mathlib import Vector

from ...resource.strings import build_module_strings

from ..damage_hook import (
    get_hook, is_world, protected_player_manager,
    strings_module as strings_damage_hook)

from ..equipment_switcher import saved_player_manager

from ..players import main_player_manager

from ..rebels import register_rebel_filter

from ..show_damage import show_damage

from ..teams import GUARDS_TEAM

from .survival import SurvivalPlayerBasedFriendlyFire
from .survival import SurvivalTeamBasedFriendlyFire

from . import (
    add_available_game, stage)


strings_module = build_module_strings('games/survival_knockout')


def push_by_damage_info(victim, attacker, info, map_data):
    # TODO: When damage_hook module is refactored, use TakeDamageInfo instead
    inflictor = Entity(info.inflictor)
    d = victim.origin - inflictor.origin

    dmg_base = map_data['ARENA_DAMAGE_BASE']
    base_force_h = map_data['ARENA_HORIZONTAL_FORCE_BASE']
    force_v = map_data['ARENA_VERTICAL_FORCE']

    vec_len = (d.x*d.x + d.y*d.y) ** 0.5

    if vec_len == 0.0:
        return

    f = {
        1: lambda x: x,
        2: lambda x: x ** 0.5,
        3: lambda x: x ** (1.0 / 3.0),
    }.get(map_data['ARENA_FORCE_FALLOFF'])

    if f is None:
        return

    k_h = (base_force_h / vec_len) * f(info.damage / dmg_base)
    k_v = f(info.damage / dmg_base)

    victim.base_velocity = Vector(d.x * k_h, d.y * k_h, force_v * k_v)


class SurvivalKnockoutPlayerBased(SurvivalPlayerBasedFriendlyFire):
    caption = strings_module['title knockout_playerbased']
    module = 'survival_knockout_playerbased'

    @stage('survival-equip-damage-hooks')
    def stage_survival_equip_damage_hooks(self):
        def hook_p(counter, info):
            victim = counter.owner.player

            if info.attacker == victim.index or is_world(info.attacker):
                return False

            attacker = main_player_manager[info.attacker]

            if attacker in self._players:
                show_damage(attacker, info.damage)
                push_by_damage_info(victim, attacker, info, self.map_data)

            return False

        def hook_w_min_damage(counter, info):
            if not is_world(info.attacker):
                return False

            min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
            return info.damage >= min_damage

        for player in main_player_manager.values():
            if player.dead:
                continue

            p_player = protected_player_manager[player.index]
            self._counters[player.userid] = []
            if player in self._players:
                counter1 = p_player.new_counter(
                    display=strings_damage_hook['health against_guards'])

                counter1.hook_hurt = get_hook('G')

                counter2 = p_player.new_counter()
                counter2.hook_hurt = hook_p

                counter3 = p_player.new_counter()
                counter3.hook_hurt = hook_w_min_damage
                counter3.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid].append(counter1)
                self._counters[player.userid].append(counter2)
                self._counters[player.userid].append(counter3)

            elif player.team == GUARDS_TEAM:
                counter = p_player.new_counter()
                if self.map_data['ALLOW_REBELLING']:
                    counter.hook_hurt = get_hook('SWP')
                    counter.display = strings_damage_hook[
                        'health against_prisoners']

                else:
                    counter.hook_hurt = get_hook('SW')
                    counter.display = strings_damage_hook['health general']

                self._counters[player.userid].append(counter)

            p_player.set_protected()

        if not self.map_data['ALLOW_REBELLING']:
            def rebel_filter(player):
                return player not in self._players_all

            self._rebel_filter = rebel_filter
            register_rebel_filter(rebel_filter)

add_available_game(SurvivalKnockoutPlayerBased)


class SurvivalKnockoutTeamBased(SurvivalTeamBasedFriendlyFire):
    caption = strings_module['title knockout_teambased']
    module = 'survival_knockout_teambased'

    @stage('survival-equip-damage-hooks')
    def stage_survival_equip_damage_hooks(self):
        if self.map_data['RESTORE_HEALTH_ON_FF']:
            def hook_p(counter, info):
                victim = counter.owner.player

                if info.attacker == victim.index or is_world(info.attacker):
                    return False

                attacker = main_player_manager[info.attacker]

                try:
                    attacker_team = self.get_player_team(attacker)
                    victim_team = self.get_player_team(victim)
                except IndexError:
                    return False

                if attacker_team == victim_team:
                    return False

                show_damage(attacker, info.damage)
                push_by_damage_info(victim, attacker, info, self.map_data)

                return False

        else:
            def hook_p(counter, info):
                victim = counter.owner.player

                if info.attacker == victim.index or is_world(info.attacker):
                    return False

                attacker = main_player_manager[info.attacker]

                if attacker not in self._players:
                    return False

                show_damage(attacker, info.damage)
                push_by_damage_info(victim, attacker, info, self.map_data)

                return False

        def hook_w_min_damage(counter, info):
            if not is_world(info.attacker):
                return False

            min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
            return info.damage >= min_damage

        for player in main_player_manager.values():
            if player.dead:
                continue

            p_player = protected_player_manager[player.index]
            self._counters[player.userid] = []
            if player in self._players:
                counter1 = p_player.new_counter(
                    display=strings_damage_hook['health against_guards'])

                counter1.hook_hurt = get_hook('G')

                counter2 = p_player.new_counter()
                counter2.hook_hurt = hook_p

                counter3 = p_player.new_counter()
                counter3.hook_hurt = hook_w_min_damage
                counter3.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid].append(counter1)
                self._counters[player.userid].append(counter2)
                self._counters[player.userid].append(counter3)

            elif player.team == GUARDS_TEAM:
                counter = p_player.new_counter()
                if self.map_data['ALLOW_REBELLING']:
                    counter.hook_hurt = get_hook('SWP')
                    counter.display = strings_damage_hook[
                        'health against_prisoners']

                else:
                    counter.hook_hurt = get_hook('SW')
                    counter.display = strings_damage_hook['health general']

                self._counters[player.userid].append(counter)

            p_player.set_protected()

        if not self.map_data['ALLOW_REBELLING']:
            def rebel_filter(player):
                return player not in self._players_all

            self._rebel_filter = rebel_filter
            register_rebel_filter(rebel_filter)

add_available_game(SurvivalKnockoutTeamBased)
