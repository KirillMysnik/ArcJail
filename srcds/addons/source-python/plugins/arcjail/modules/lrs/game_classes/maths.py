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

from ...games.game_classes.maths import strings_module as strings_games

from ..base_classes.chat_game import ChatGame

from .. import add_available_game, stage


MIN_OPERATIONS = 2
MAX_OPERATIONS = 4
MIN_SUMMAND_VALUE = 0
MAX_SUMMAND_VALUE = 50


class Maths(ChatGame):
    caption = strings_games['title']
    rules = [
        strings_games['rules 1'],
    ]

    @stage('chatgame-generate-test')
    def stage_chatgame_generate_test(self):
        expr = ""
        answer = 0
        for i in range(randint(MIN_OPERATIONS, MAX_OPERATIONS)):
            summand = randint(MIN_SUMMAND_VALUE, MAX_SUMMAND_VALUE)
            if randint(0, 1):
                expr += "+"
                answer += summand
            else:
                expr += "-"
                answer -= summand

            expr += str(summand)

        if expr.startswith("+"):
            expr = expr[1:]

        self._game_data['expr'] = expr
        self._game_data['answer'] = str(answer)
        self._question = strings_games['question'].tokenize(expr=expr)

    def answer_accepted(self, player, message):
        if message != self._game_data['answer']:
            return

        loser = self.guard if player == self.prisoner else self.prisoner

        self._results['winner'] = player
        self._results['loser'] = loser

        self.set_stage_group('win')

add_available_game(Maths)
