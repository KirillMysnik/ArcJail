from warnings import warn

from ..damage_hook import (
    get_hook, protected_player_manager, strings_module as strings_damage_hook)

from ..equipment_switcher import saved_player_manager

from ..falldmg_protector import protect as falldmg_protect

from ..games.survival import (
    PossibleDeadEndWarning, strings_module as strings_games)

from ..overlays import show_overlay

from .base_classes.map_game import MapGame
from .base_classes.map_game_team_based import MapGameTeamBased

from . import (
    add_available_game, game_event_handler, config_manager, push, stage)


def build_survival_base(*parent_classes):
    class SurvivalBase(*parent_classes):
        stage_groups = {
            'mapgame-start': [
                "mapgame-equip-weapons",
                "mapgame-register-push-handlers",
                "mapgame-apply-cvars",
                "mapgame-fire-mapdata-outputs",
                "mapgame-entry",
            ],
            'mapgame-prepare': [
                "mapgame-cancel-falldmg-protection",
                "mapgame-equip-noblock",
                "mapgame-swap-guard",
                "survival-equip-damage-hooks",
                "mapgame-teleport-players",
                "mapgame-fire-mapdata-prepare-outputs",
                "mapgame-prepare-entry",
            ],
            'destroy': [
                "prepare-cancel-delays",
                "unsend-popups",
                "destroy",
                "survival-fall-protection",
            ],
        }

        def __init__(self, players, **kwargs):
            super().__init__(players, **kwargs)

            self._counters = {}
            self._flawless = {
                self.prisoner.userid: True,
                self.guard.userid: True,
            }

        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            def hook_hurt_for_prisoner(counter, game_event):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
                current_damage = game_event.get_int('dmg_health')

                if current_damage >= min_damage:
                    self._flawless[self.prisoner.userid] = False
                    return True

                return False

            def hook_death_for_prisoner(counter, game_event):
                saved_player = saved_player_manager[self.prisoner.userid]
                saved_player.strip()
                return True

            def death_callback_for_prisoner():
                self.on_death(self.prisoner)

            def hook_hurt_for_guard(counter, game_event):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']
                current_damage = game_event.get_int('dmg_health')

                if current_damage >= min_damage:
                    self._flawless[self.guard.userid] = False
                    return True

                return False

            def hook_death_for_guard(counter, game_event):
                saved_player = saved_player_manager[self.guard.userid]
                saved_player.strip()
                return True

            def death_callback_for_guard():
                self.on_death(self.guard)

            for hook_hurt, hook_death, death_callback, player in zip(
                    (hook_hurt_for_prisoner, hook_hurt_for_guard),
                    (hook_death_for_prisoner, hook_death_for_guard),
                    (death_callback_for_prisoner, death_callback_for_guard),
                    self._players
            ):

                p_player = protected_player_manager[player.userid]
                counter = p_player.new_counter(
                    display=strings_damage_hook['health game'])

                if self.map_data['ALLOW_SELFDAMAGE']:
                    counter.hook_hurt = get_hook('SW', next_hook=hook_hurt)

                else:
                    warn(PossibleDeadEndWarning(
                        "Self-damage is disabled and it's a non-ff game! "
                        "Players may have problems dying. "
                        "Tell map creator about this problem."))

                    counter.hook_hurt = get_hook('', next_hook=hook_hurt)

                counter.hook_death = hook_death
                counter.death_callback = death_callback
                counter.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid] = counter

                p_player.set_protected()

        @stage('undo-survival-equip-damage-hooks')
        def stage_undo_survival_equip_damage_hooks(self):
            for player in self._players_all:
                p_player = protected_player_manager[player.userid]
                p_player.delete_counter(self._counters[player.userid])
                p_player.unset_protected()

        @stage('survival-fall-protection')
        def stage_survival_fall_protection(self):
            for player in self._players:
                falldmg_protect(player, self.map_data)

        def on_death(self, player):
            if player == self.prisoner:
                winner, loser = self.guard, self.prisoner
            else:
                winner, loser = self.prisoner, self.guard

            if self._flawless[winner.userid]:
                if config_manager['flawless_sound'] is not None:
                    indexes = [player_.index for player_ in self._players]
                    config_manager['flawless_sound'].play(*indexes)

                if config_manager['flawless_material'] != "":
                    for player in self._players:
                        show_overlay(
                            player, config_manager['flawless_material'], 3)

            self._results['winner'] = winner
            self._results['loser'] = loser

            self.set_stage_group('win')

        @push(None, 'end_game')
        def push_end_game(self, args):
            self.set_stage_group('abort-map-cancelled')

        @game_event_handler('jailgame-player-death', 'player_death')
        def event_jailgame_player_death(self, game_event):
            pass

    return SurvivalBase


class SurvivalPlayerBased(build_survival_base(MapGame)):
    caption = strings_games['title playerbased_standard']
    module = 'survival_playerbased_standard'

add_available_game(SurvivalPlayerBased)


class SurvivalTeamBased(build_survival_base(MapGameTeamBased)):
    caption = strings_games['title teambased_standard']
    module = 'survival_teambased_standard'

add_available_game(SurvivalTeamBased)