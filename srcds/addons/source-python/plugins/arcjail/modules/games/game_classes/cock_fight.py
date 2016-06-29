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

from random import choice

from engines.sound import Sound
from entities.constants import INVALID_ENTITY_INTHANDLE
from listeners.tick import on_tick_listener_manager

from controlled_cvars.handlers import bool_handler, int_handler

from ....arcjail import InternalEvent, load_downloadables

from ....resource.strings import build_module_strings

from ...players import broadcast, main_player_manager

from ... import build_module_config

from ..base_classes.prepare_time import PrepareTime

from .. import (
    add_available_game, game_event_handler, helper_set_loser,
    helper_set_winner, stage)


strings_module = build_module_strings('games/cock_fight')
config_manager = build_module_config('games/cock_fight')

config_manager.controlled_cvar(
    bool_handler,
    "enabled",
    default=1,
    description="Enable/Disable Cock Fight (game)"
)
config_manager.controlled_cvar(
    int_handler,
    "percentage",
    default=50,
    description="Alive players percentage when the game ends"
)
config_manager.controlled_cvar(
    bool_handler,
    "sounds",
    default=1,
    description="Enable/disable chicken sounds"
)
config_manager.controlled_cvar(
    int_handler,
    "jump_force",
    default=256,
    description="Vertical force to apply to the cock when it has "
                "climbed onto somebody",
)

_downloadables_sounds = load_downloadables('cockfight-sounds.res')
sounds = []
for line in _downloadables_sounds:
    sounds.append(line[len("sound/"):])


class CockFight(PrepareTime):
    caption = strings_module['title']
    stage_groups = {
        'cockfight-register-tick': ["cockfight-register-tick", ],
    }

    def __init__(self, leader_player, players, **kwargs):
        super().__init__(leader_player, players, **kwargs)

        self._score = 0
        self._max_score = 0

    def _tick(self):
        for player in self._players:
            # Force player to crouch
            try:
                player.flags |= 2
            except RuntimeError:
                continue

            # Check if player has climbed onto another player
            if player.ground_entity == INVALID_ENTITY_INTHANDLE:
                continue

            for player_ in self._players:
                if player_ == player:
                    continue

                if player_.inthandle == player.ground_entity:
                    if config_manager['jump_force']:
                        player.push(0, config_manager['jump_force'],
                                    vert_override=True)

                    helper_set_loser(player_, effects=False)
                    self._score -= 1

                    current_score = (
                        self._max_score * config_manager['percentage'] / 100)

                    if self._score <= current_score:
                        names = []
                        winners = []
                        for player__ in self._players:
                            if player__ == player_:
                                continue

                            helper_set_winner(player__)
                            names.append(player__.name)
                            winners.append(player__)

                        broadcast(strings_module['players_alive'].tokenize(
                                  players=' '.join(names)))

                        InternalEvent.fire(
                            'jail_game_cock_fight_winners',
                            winners=winners,
                            starting_player_number=self._max_score,
                        )

                        self.set_stage_group('destroy')

                    else:
                        broadcast(strings_module['player_out'].tokenize(
                            player=player_.name))

                    if self._settings.get('training', False):
                        self._players.remove(player_)

                    else:
                        # TODO: If we specify attacker index,
                        # it won't do any damage - why?
                        player_.take_damage(player_.health)

                    break

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self._score = len(self._players)
        self._max_score = len(self._players)

        self.set_stage_group('cockfight-register-tick')

    @stage('cockfight-register-tick')
    def stage_cockfight_register_tick(self):
        on_tick_listener_manager.register_listener(self._tick)

    @stage('undo-cockfight-register-tick')
    def stage_undo_cockfight_register_tick(self):
        on_tick_listener_manager.unregister_listener(self._tick)

    @game_event_handler('cockfight-player-jump', 'player_jump')
    def event_cockfight_player_jump(self, game_event):
        if not config_manager['sounds']:
            return

        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if player in self.players:
            sound_name = choice(sounds)
            sound = Sound(sound_name, player.index)
            sound.play()


add_available_game(CockFight)
