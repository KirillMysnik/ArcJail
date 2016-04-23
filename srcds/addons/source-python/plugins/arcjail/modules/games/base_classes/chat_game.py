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

from random import randrange

from listeners.tick import Delay

from controlled_cvars.handlers import (
    bool_handler, float_handler, int_handler, sound_nullable_handler)

from ....resource.strings import build_module_strings

from ...players import broadcast, main_player_manager, tell

from ... import build_module_config

from .. import (
    game_event_handler, helper_set_neutral, helper_set_winner, stage,
    strings_module as strings_games)

from .player_preserving import PlayerPreserving


config_manager = build_module_config('lrs/chat_game')
strings_module = build_module_strings('lrs/chat_game')

config_manager.controlled_cvar(
    float_handler,
    "rules_print_interval",
    default=2,
    description="Interval (in seconds) in printing game rules to chat"
)
config_manager.controlled_cvar(
    float_handler,
    "answer_timeout",
    default=20,
    description="Delay (in seconds) after the question has been asked "
                "before failing and doing a replay"
)
config_manager.controlled_cvar(
    int_handler,
    "replays_number",
    default=2,
    description="Number of allowed replays before the game is aborted."
                "Initial (first) play is not included. -1 to disable limit "
                "(not recommended)."
)
config_manager.controlled_cvar(
    bool_handler,
    "allow_multiple_attempts",
    default=1,
    description="Allow/Disallow multiple answer attemps in one replay"
)
config_manager.controlled_cvar(
    sound_nullable_handler,
    "sound",
    default="buttons/bell1.wav",
    description="Sound to play when the question is asked, leave empty "
                "to disable"
)
config_manager.controlled_cvar(
    float_handler,
    "ask_delay_min",
    default=0.0,
    description="Minimum ask delay (in seconds)"
)
config_manager.controlled_cvar(
    float_handler,
    "ask_delay_max",
    default=5.0,
    description="Maximum ask delay (in seconds)"
)


class ChatGame(PlayerPreserving):
    rules = []
    stage_groups = {
        'chatgame-print-rules': ["chatgame-print-rules", ],
        'chatgame-improperly-configured': ["chatgame-improperly-configured", ],
        'chatgame-start': [
            "chatgame-generate-test",
            "chatgame-prepare-to-ask",
        ],
        'chatgame-ask': ["chatgame-ask", ],
        'chatgame-timed-out': ["chatgame-timed-out", ],
        'chatgame-replay': [
            "chatgame-reset",
            "chatgame-generate-test",
            "chatgame-prepare-to-ask",
        ],
        'game-end-player-won': ['game-end-player-won', ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._results = {}

        self._answers = {}
        self._answers_order = []

        self._rules_print = 0
        self._times_replayed = 0

        self._game_data = {}
        self._question = None
        self._receiving_answers = False

    @stage('game-end-player-won')
    def stage_game_end_player_won(self):
        winner = self._results['winner']

        broadcast(strings_games['win_player'].tokenize(player=winner.name))

        for player in self._players_all:
            if player == winner:
                helper_set_winner(player)

            else:
                helper_set_neutral(player)

        self.set_stage_group('destroy')

    @stage('nooffensegame-entry')
    def stage_nooffensegame_entry(self):
        self.set_stage_group('chatgame-print-rules')

    @stage('chatgame-print-rules')
    def stage_chatgame_print_rules(self):
        if self._rules_print == len(self.rules):
            self.set_stage_group('chatgame-start')

        else:
            rule = self.rules[self._rules_print]
            broadcast(rule)

            self._rules_print += 1

            def callback():
                self.set_stage_group('chatgame-print-rules')

            self._delays.append(Delay(
                config_manager['rules_print_interval'], callback
            ))

    @stage('chatgame-generate-test')
    def stage_chatgame_generate_test(self):
        raise NotImplementedError

    @stage('chatgame-prepare-to-ask')
    def stage_prepare_prepare_to_ask(self):
        def ask_callback():
            self.set_stage_group('chatgame-ask')

        min_delay = max(0, config_manager['ask_delay_min'])
        max_delay = min(0, config_manager['ask_delay_min'])

        if min_delay > max_delay:
            self.set_stage_group('chatgame-improperly-configured')
            return

        if min_delay == max_delay:
            delay = min_delay
        else:
            delay = randrange(min_delay, max_delay)

        self._delays.append(Delay(delay, ask_callback))

    @stage('chatgame-improperly-configured')
    def stage_chatgame_improperly_configured(self):
        broadcast(strings_module['improper_configuration'])
        self.set_stage_group('destroy')

    @stage('chatgame-ask')
    def stage_chatgame_ask(self):
        timeout = max(1, config_manager['answer_timeout'])

        def timeout_callback():
            self.set_stage_group('chatgame-timed-out')

        self._delays.append(Delay(timeout, timeout_callback))

        broadcast(self._question)

        if config_manager['sound'] is not None:
            indexes = [player.index for player in self._players]
            config_manager['sound'].play(*indexes)

        self._receiving_answers = True

    @stage('chatgame-timed-out')
    def stage_chatgame_timed_out(self):
        if (config_manager['replays_number'] != -1 and
                (
                            self._times_replayed >=
                            config_manager['replays_number']
                )
        ):

            broadcast(strings_module['too_many_replays'])
            self.set_stage_group('draw')

        else:
            self._receiving_answers = False
            broadcast(strings_module['replaying'])

            self._times_replayed += 1
            self.set_stage_group('chatgame-replay')

    @stage('chatgame-reset')
    def stage_chatgame_reset(self):
        self._answers = {}
        self._answers_order = []
        self._game_data = {}
        self._question = None
        self._receiving_answers = False

    @game_event_handler('chatgame-player-say', 'player_say')
    def event_chatgame_player_say(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        message = game_event.get_string('text')

        if player not in self._players:
            return

        if not self._receiving_answers:
            tell(player, strings_module['no_question_yet'])
            return

        if (player.index in self._answers and
                not config_manager['allow_multiple_attempts']):
            tell(player, strings_module['already_answered'])
            return

        self._answers[player.index] = message

        if player.index in self._answers_order:
            self._answers_order.remove(player.index)
        self._answers_order.append(player.index)

        tell(player, strings_module['answer_accepted'])

        self.answer_accepted(player, message)

    def answer_accepted(self, player, message):
        raise NotImplementedError
