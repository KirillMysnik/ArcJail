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

from listeners.tick import Delay

from controlled_cvars.handlers import float_handler

from ...resource.strings import build_module_strings

from ..damage_hook import get_hook, protected_player_manager

from ..players import main_player_manager

from .. import build_module_config

from .base_classes.jail_game import JailGame

from . import game_event_handler, stage


strings_module = build_module_strings('lrs/win_reward')
config_manager = build_module_config('lrs/win_reward')

config_manager.controlled_cvar(
    float_handler,
    "duration",
    default=10,
    description="Duration of Win Reward"
)
config_manager.controlled_cvar(
    float_handler,
    "loser_speed",
    default=0.5,
    description="Loser's speed"
)


class WinReward(JailGame):
    caption = "Win Reward"
    stage_groups = {
        'winreward-start': [
            "equip-damage-hooks",
            "set-start-status",
            "winreward-entry",
        ],
        'winreward-timed-out': ["winreward-timed-out", ],
    }

    def __init__(self, players, **kwargs):
        super().__init__(players, **kwargs)

        self._counters = {}
        self._results = {
            'winner': kwargs['winner'],
            'loser': kwargs['loser'],
        }

    @stage('basegame-entry')
    def stage_basegame_entry(self):
        self.set_stage_group('winreward-start')

    @stage('equip-damage-hooks')
    def stage_equip_damage_hooks(self):
        winner, loser = self._results['winner'], self._results['loser']

        def hook_hurt_for_loser(counter, info):
            return info.attacker == winner.index

        for player in self._players:
            p_player = protected_player_manager[player.index]

            counter = self._counters[player.index] = p_player.new_counter()

            if player == winner:
                counter.hook_hurt = get_hook('SW')
            else:
                counter.hook_hurt = hook_hurt_for_loser

            p_player.set_protected()

    @stage('undo-equip-damage-hooks')
    def stage_undo_equip_damage_hooks(self):
        for player in self._players_all:
            p_player = protected_player_manager[player.index]
            p_player.delete_counter(self._counters[player.index])
            p_player.unset_protected()

    @stage('winreward-entry')
    def stage_winreward_entry(self):
        winner, loser = self._results['winner'], self._results['loser']

        loser.speed = config_manager['loser_speed']

        def timeout_callback():
            self.set_stage_group('winreward-timed-out')

        self._delays.append(
            Delay(config_manager['duration'], timeout_callback))

    @stage('winreward-timed-out')
    def stage_wireward_timed_out(self):
        winner, loser = self._results['winner'], self._results['loser']

        loser.take_damage(loser.health, attacker_index=winner.index)

    @game_event_handler('jailgame-player-death', 'player_death')
    def event_jailgame_player_death(self, game_event):
        player = main_player_manager.get_by_userid(
            game_event.get_int('userid'))

        if player not in self._players:
            return

        self._players.remove(player)

        winner, loser = self._results['winner'], self._results['loser']

        if player == winner:
            loser.take_damage(loser.health + 1, attacker_index=winner.index)

        self.set_stage_group('destroy')
