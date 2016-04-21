from ...equipment_switcher import saved_player_manager

from ...damage_hook import is_world, protected_player_manager

from ...games.survival_knockout import (
    push_by_damage_info, strings_module as strings_games)

from ...players import main_player_manager

from ...show_damage import show_damage

from .. import add_available_game, stage

from .survival import (
    SurvivalPlayerBasedFriendlyFire, SurvivalTeamBasedFriendlyFire)


def build_survival_knockout_base(*parent_classes):
    class SurvivalKnockoutBase(*parent_classes):
        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            for player in self._players:
                p_player = protected_player_manager[player.index]
                self._counters[player.userid] = []

                def hook_on_death(counter, game_event, player=player):
                    saved_player = saved_player_manager[player.index]
                    saved_player.strip()
                    return True

                def hook_game_player(counter, info, player=player):
                    if (info.attacker == player.index or
                            is_world(info.attacker)):

                        return False

                    attacker = main_player_manager[info.attacker]
                    if attacker in self._players:
                        self._flawless[player.userid] = False
                        show_damage(attacker, info.damage)
                        push_by_damage_info(
                            player, attacker, info, self.map_data)

                    return False

                def hook_w_min_damage(counter, info):
                    if not is_world(info.attacker):
                        return False

                    min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
                    return info.damage >= min_damage

                counter1 = p_player.new_counter()
                counter1.hook_hurt = hook_game_player

                counter2 = p_player.new_counter()
                counter2.hook_hurt = hook_w_min_damage
                counter2.hook_death = hook_on_death
                counter2.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid].append(counter1)
                self._counters[player.userid].append(counter2)

                p_player.set_protected()

    return SurvivalKnockoutBase


class SurvivalKnockoutPlayerBased(
        build_survival_knockout_base(SurvivalPlayerBasedFriendlyFire)):

    caption = strings_games['title knockout_playerbased']
    module = 'survival_knockout_playerbased'

add_available_game(SurvivalKnockoutPlayerBased)


class SurvivalKnockoutTeamBased(
        build_survival_knockout_base(SurvivalTeamBasedFriendlyFire)):

    caption = strings_games['title knockout_teambased']
    module = 'survival_knockout_teambased'

add_available_game(SurvivalKnockoutTeamBased)
