from ...resource.strings import build_module_strings

from ..damage_hook import get_hook, protected_player_manager

from ..games.scoregames import config_manager as config_manager_games

from ..overlays import show_overlay

from ..players import broadcast

from .base_classes.map_game_team_based import MapGameTeamBased

from . import (
    add_available_game, config_manager as config_manager_common, push, stage)


strings_module = build_module_strings('lrs/scoregames')

class ScoreGameBase(MapGameTeamBased):
    stage_groups = {
        'scoregame-new-score2': ['scoregame-new-score2', ],
        'scoregame-check-team-scores': ['scoregame-check-team-scores', ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self.score = {
            self.prisoner.userid: 0,
            self.guard.userid: 0,
        }
        self.win_score = (self.map_data['MAX_SCORE'] if
                          self.map_data['MAX_SCORE'] > 0 else
                          config_manager_games['win_score'])

    @stage('scoregame-new-score2')
    def stage_scoregame_new_score2(self):
        broadcast(strings_module['new_score2'].tokenize(
            player1=self.prisoner.name,
            score1=self.score[self.prisoner.userid],
            player2=self.guard.name,
            score2=self.score[self.guard.userid]
        ))

        self.set_stage_group('scoregame-check-team-scores')

    @stage('scoregame-check-team-scores')
    def stage_scoregame_check_team_scores(self):
        if self.score[self.prisoner.userid] == self.win_score:
            winner, loser = self.prisoner, self.guard

        elif self.score[self.guard.userid] == self.win_score:
            winner, loser = self.guard, self.prisoner

        else:
            return

        self._results['winner'] = winner
        self._results['loser'] = loser

        if self.score[loser.userid] == 0:
            if config_manager_common['flawless_sound'] is not None:
                indexes = [player_.index for player_ in self._players]
                config_manager_common['flawless_sound'].play(*indexes)

            if config_manager_common['flawless_material'] != "":
                for player in self._players:
                    show_overlay(
                        player, config_manager_common['flawless_material'], 3)

        self.set_stage_group('win')

    @push(None, 'end_game')
    def push_end_game(self, args):
        if self.score[self.prisoner.userid] > self.score[self.guard.userid]:
            winner, loser = self.prisoner, self.guard
        elif self.score[self.prisoner.userid] < self.score[self.guard.userid]:
            winner, loser = self.guard, self.prisoner
        else:
            self.set_stage_group('draw')
            return

        self._results['winner'] = winner
        self._results['loser'] = loser

        if self.score[loser.userid] == 0:
            if config_manager_common['flawless_sound'] is not None:
                indexes = [player_.index for player_ in self._players]
                config_manager_common['flawless_sound'].play(*indexes)

            if config_manager_common['flawless_material'] != "":
                for player in self._players:
                    show_overlay(
                        player, config_manager_common['flawless_material'], 3)

        self.set_stage_group('win')

    @push(None, 'scoregames_score_point')
    def push_scoregames_score_point(self, args):
        try:
            team_num = int(args[0])
            assert 1 <= team_num <= 2
        except (IndexError, ValueError, AssertionError):
            return

        if team_num == 1:
            self.score[self.prisoner.userid] += 1
        else:
            self.score[self.guard.userid] += 1

        self.set_stage_group('scoregame-new-score2')


class ScoreGameStandard(ScoreGameBase):
    caption = strings_module['title standard']
    module = 'scoregame_standard'

add_available_game(ScoreGameStandard)


class ScoreGameAllowDeaths(ScoreGameBase):
    caption = strings_module['title allowdeaths']
    module = 'scoregame_allowdeaths'

add_available_game(ScoreGameAllowDeaths)


class ScoreGameNoPropKill(ScoreGameBase):
    caption = strings_module['title nopropkill']
    module = 'scoregame_nopropkill'

    stage_groups = {
        'mapgame-prepare': [
            "mapgame-cancel-falldmg-protection",
            "mapgame-equip-noblock",
            "scoregame-equip-damage-hooks",
            "mapgame-swap-guard",
            "mapgame-teleport-players",
            "mapgame-fire-mapdata-prepare-outputs",
            "mapgame-prepare-entry",
        ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._counters = {}

    @stage('scoregame-equip-damage-hooks')
    def stage_scoregame_equip_damage_hooks(self):
        for player in self._players:
            p_player = protected_player_manager[player.userid]

            self._counters[player.userid] = p_player.new_counter()
            self._counters[player.userid].hook_hurt = get_hook('')

            p_player.set_protected()

    @stage('undo-scoregame-equip-damage-hooks')
    def stage_undo_scoregame_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.userid]
            p_player.delete_counter(self._counters[player.userid])
            p_player.unset_protected()

add_available_game(ScoreGameNoPropKill)
