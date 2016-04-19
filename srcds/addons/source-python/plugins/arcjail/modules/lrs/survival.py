from warnings import warn

from cvars import ConVar

from ..damage_hook import (
    get_hook, is_world, protected_player_manager,
    strings_module as strings_damage_hook)

from ..equipment_switcher import saved_player_manager

from ..falldmg_protector import protect as falldmg_protect

from ..games.survival import (
    PossibleDeadEndWarning, strings_module as strings_games)

from ..games import play_flawless_effects

from ..no_ff_spam import (
    disable as no_ff_spam_disable, enable as no_ff_spam_enable)

from ..players import main_player_manager

from ..show_damage import show_damage

from ..silent_cvars import silent_set

from ..teams import GUARDS_TEAM, PRISONERS_TEAM

from .base_classes.map_game import MapGame
from .base_classes.map_game_team_based import MapGameTeamBased

from . import (
    add_available_game, game_event_handler, push, stage)


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
            def hook_hurt_for_prisoner(counter, info):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                if info.damage >= min_damage:
                    self._flawless[self.prisoner.userid] = False
                    return True

                return False

            def hook_death_for_prisoner(counter, game_event):
                saved_player = saved_player_manager[self.prisoner.index]
                saved_player.strip()
                return True

            def hook_hurt_for_guard(counter, info):
                min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                if info.damage >= min_damage:
                    self._flawless[self.guard.userid] = False
                    return True

                return False

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
                counter.health = self.map_data['INITIAL_HEALTH']

                self._counters[player.userid] = counter

                p_player.set_protected()

        @stage('undo-survival-equip-damage-hooks')
        def stage_undo_survival_equip_damage_hooks(self):
            for player in self._players_all:
                p_player = protected_player_manager[player.index]
                p_player.delete_counter(self._counters[player.userid])
                p_player.unset_protected()

        @stage('survival-fall-protection')
        def stage_survival_fall_protection(self):
            for player in self._players:
                falldmg_protect(player, self.map_data)

        @game_event_handler('jailgame-player-death', 'player_death')
        def event_jailgame_player_death(self, game_event):
            player = main_player_manager.get_by_userid(
                game_event.get_int('userid'))

            if player == self.prisoner:
                winner, loser = self.guard, self.prisoner
            else:
                winner, loser = self.prisoner, self.guard

            if self._flawless[winner.userid]:
                play_flawless_effects(self._players)

            self._results['winner'] = winner
            self._results['loser'] = loser

            self.set_stage_group('win')

        @push(None, 'end_game')
        def push_end_game(self, args):
            self.set_stage_group('abort-map-cancelled')

    return SurvivalBase


class SurvivalPlayerBased(build_survival_base(MapGame)):
    caption = strings_games['title playerbased_standard']
    module = 'survival_playerbased_standard'

add_available_game(SurvivalPlayerBased)


class SurvivalTeamBased(build_survival_base(MapGameTeamBased)):
    caption = strings_games['title teambased_standard']
    module = 'survival_teambased_standard'

add_available_game(SurvivalTeamBased)


def build_survival_friendlyfire_base(*parent_classes):
    class SurvivalFriendlyFireBase(*parent_classes):
        cvar_friendlyfire = ConVar('mp_friendlyfire')

        stage_groups = {
            'mapgame-start': [
                "mapgame-equip-weapons",
                "mapgame-register-push-handlers",
                "mapgame-apply-cvars",
                "mapgame-fire-mapdata-outputs",
                "survival-enable-ff",
                "mapgame-entry",
            ]
        }

        @stage('survival-enable-ff')
        def stage_survival_enable_ff(self):
            no_ff_spam_enable()

            self._cvars['friendlyfire'] = self.cvar_friendlyfire.get_bool()

            silent_set(self.cvar_friendlyfire, 'bool', True)

        @stage('undo-survival-enable-ff')
        def stage_undo_survival_enable_ff(self):
            no_ff_spam_disable()

            silent_set(
                self.cvar_friendlyfire, 'bool', self._cvars['friendlyfire'])

        @stage('survival-equip-damage-hooks')
        def stage_survival_equip_damage_hooks(self):
            for player in main_player_manager.values():
                if player.dead:
                    continue

                p_player = protected_player_manager[player.index]

                if player in self._players:
                    def hook_on_death(counter, game_event, player=player):
                        saved_player = saved_player_manager[player.index]
                        saved_player.strip()

                        return True

                    def hook_min_damage(counter, info, player=player):
                        min_damage = self.map_data['ARENA_MIN_DAMAGE_TO_HURT']

                        if info.damage >= min_damage:
                            self._flawless[player.userid] = False
                            return True

                        return False

                    def hook_game_p(counter, info, player=player):
                        if (info.attacker == player.index or
                                is_world(info.attacker)):

                            return False

                        attacker = main_player_manager[info.attacker]
                        if attacker in self._players:
                            show_damage(attacker, info.damage)
                            return hook_min_damage(counter, info)

                        return False

                    def hook_sw_game_p(counter, info, player=player):
                        if (info.attacker == player.index or
                                is_world(info.attacker)):

                            return hook_min_damage(counter, info)

                        attacker = main_player_manager[info.attacker]
                        if attacker in self._players:
                            show_damage(attacker, info.damage)
                            return hook_min_damage(counter, info)

                        return False

                    counter = p_player.new_counter(
                        display=strings_damage_hook['health game'])

                    if self.map_data['ALLOW_SELFDAMAGE']:
                        counter.hook_hurt = hook_sw_game_p
                    else:
                        counter.hook_hurt = hook_game_p

                    counter.hook_death = hook_on_death
                    counter.health = self.map_data['INITIAL_HEALTH']

                    self._counters[player.userid] = counter
                    p_player.set_protected()

                elif player.team == GUARDS_TEAM:
                    def hook_sw_nongame_p(counter, info, player=player):
                        if (info.attacker == player.index or
                                is_world(info.attacker)):

                            return True

                        attacker = main_player_manager[info.attacker]
                        if attacker in self._players:
                            return False

                        if attacker.team == GUARDS_TEAM:
                            return False

                        return True

                    counter = p_player.new_counter()
                    counter.hook_hurt = hook_sw_nongame_p
                    counter.display = strings_damage_hook['health general']

                    self._counters[player.userid] = counter
                    p_player.set_protected()

                elif player.team == PRISONERS_TEAM:
                    counter = p_player.new_counter()
                    counter.hook_hurt = get_hook('SWG')
                    counter.display = strings_damage_hook['health general']

                    self._counters[player.userid] = counter
                    p_player.set_protected()

    return SurvivalFriendlyFireBase


class SurvivalTeamBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalTeamBased)):

    caption = strings_games['title teambased_friendlyfire']
    module = 'survival_teambased_friendlyfire'

add_available_game(SurvivalTeamBasedFriendlyFire)


class SurvivalPlayerBasedFriendlyFire(
        build_survival_friendlyfire_base(SurvivalPlayerBased)):

    caption = strings_games['title playerbased_friendlyfire']
    module = 'survival_playerbased_friendlyfire'

add_available_game(SurvivalPlayerBasedFriendlyFire)
