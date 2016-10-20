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

from listeners import OnClientDisconnect

from spam_proof_commands.say import SayCommand

from ...internal_events import InternalEvent
from ...resource.strings import build_module_strings

from ..arcjail import strings_module as strings_arcjail
from ..arcjail.arcjail_user import arcjail_user_manager
from ..credits import earn_credits, spend_credits
from ..lrs import LastRequestGameStatus
from ..lrs.win_reward import WinReward
from ..players import broadcast, tell


ANTI_SPAM_TIMEOUT = 1


strings_module = build_module_strings('credits/bets')
current_sweepstakes = None


class Sweepstakes(dict):
    class Bet:
        def __init__(self, player, credits_, target):
            self.player = player
            self.credits = credits_
            self.target = target

    def __init__(self):
        super().__init__()

        self._accepting = True

    @property
    def caption(self):
        raise NotImplementedError

    @property
    def accepting(self):
        return self._accepting

    def stop_bet_accepting(self):
        self._accepting = False

        broadcast(strings_module['sweepstakes accepting_stopped'].tokenize(
            caption=self.caption))

    def try_bet(self, player, credits_, target_raw):
        if not self._accepting:
            return strings_module['fail not_accepting']

        return None

    def abort(self):
        for bet in self.values():
            tell(bet.player, strings_module['bet returned_abort'])
            earn_credits(bet.player, bet.credits,
                         strings_module['credits_returned_reason'])

        self.clear()

    def finish(self, game_winners):
        bets_won, bets_lost = [], []
        credits_bank = 0
        for bet in self.values():
            if self.is_winning_bet(bet, game_winners):
                bets_won.append(bet)
            else:
                bets_lost.append(bet)

            credits_bank += bet.credits

        broadcast(
            strings_module['sweepstakes total_bank'], credits=credits_bank)

        winners_credits = 0
        for bet in bets_won:
            winners_credits += bet.credits

        for bet in bets_won:
            earn_credits(
                bet.player, int(bet.credits / winners_credits * credits_bank),
                strings_module['credits_earned_reason'])

        self.clear()

    def is_winning_bet(self, bet, game_winners):
        raise NotImplementedError

    def is_related(self, game_instance):
        raise NotImplementedError


class SweepstakesLR(Sweepstakes):
    def __init__(self, game_instance):
        super().__init__()

        self._game_instance = game_instance
        self._prisoner = game_instance.prisoner
        self._guard = game_instance.guard

        broadcast(strings_module['sweepstakes lr_start'])
        broadcast(strings_module['announce lr'])

    @property
    def caption(self):
        return strings_module['caption lr'].tokenize(
            prisoner=self._prisoner.name, guard=self._guard.name)

    def try_bet(self, player, credits_, target_raw):
        reason = super().try_bet(player, credits_, target_raw)
        if reason is not None:
            return reason

        if target_raw not in ("t", "ct"):
            return strings_module['fail invalid_format']

        if player.index in self:
            earn_credits(player, self[player.index].credits,
                         strings_module['credits_returned_reason'])

        if target_raw == "t":
            self[player.index] = self.Bet(player, credits_, self._prisoner)
        else:
            self[player.index] = self.Bet(player, credits_, self._guard)

        spend_credits(player, credits_, strings_module['credits_spent_reason'])

        broadcast(strings_module['bet accepted'].tokenize(
            player=player.name,
            credits=credits_,
            target=self[player.index].target.name,
        ))

        return None

    def abort(self):
        super().abort()

        self._game_instance = None

    def finish(self, game_winners):
        super().finish(game_winners)

        self._game_instance = None

    def is_winning_bet(self, bet, game_winners):
        return bet.target in game_winners

    def is_related(self, game_instance):
        return self._game_instance is game_instance


@InternalEvent('jail_lrs_status_set')
def on_jail_lrs_status_set(instance, status):
    global current_sweepstakes
    if current_sweepstakes is not None:
        return

    if status != LastRequestGameStatus.NOT_STARTED:
        return

    if isinstance(instance, WinReward):
        return

    current_sweepstakes = SweepstakesLR(instance)


@InternalEvent('jail_lr_won')
def on_jail_lr_won(winner, loser, instance):
    global current_sweepstakes
    if current_sweepstakes is None:
        return

    if not isinstance(current_sweepstakes, SweepstakesLR):
        return

    if not current_sweepstakes.is_related(instance):
        return

    current_sweepstakes.finish((winner, ))
    current_sweepstakes = None


@InternalEvent('jail_lr_destroyed')
def on_jail_lr_destroyed(instance):
    global current_sweepstakes
    if current_sweepstakes is None:
        return

    if not isinstance(current_sweepstakes, SweepstakesLR):
        return

    if not current_sweepstakes.is_related(instance):
        return

    current_sweepstakes.abort()
    current_sweepstakes = None


@InternalEvent('jail_stop_accepting_bets')
def on_jail_stop_accepting_bets(instance):
    if current_sweepstakes is None:
        return

    if not isinstance(current_sweepstakes, SweepstakesLR):
        return

    if not current_sweepstakes.is_related(instance):
        return

    if not current_sweepstakes.accepting:
        return

    current_sweepstakes.stop_bet_accepting()


@SayCommand(ANTI_SPAM_TIMEOUT, '!bet')
def say_bet(command, index, team_only):
    if current_sweepstakes is None:
        return

    arcjail_user = arcjail_user_manager[index]
    if not arcjail_user.loaded:
        tell(arcjail_user.player, strings_arcjail['not_synced'])
        return

    try:
        target = command[1]
        credits_ = command[2]
    except IndexError:
        tell(arcjail_user.player, strings_module['fail invalid_format'])
        return

    try:
        credits_ = int(credits_)
        if credits_ <= 0:
            raise ValueError
    except ValueError:
        tell(arcjail_user.player, strings_module['fail invalid_format'])
        return

    if credits_ > arcjail_user.account:
        tell(arcjail_user.player, strings_module['fail not_enough_credits'])
        return

    reason = current_sweepstakes.try_bet(arcjail_user.player, credits_, target)
    if reason is not None:
        tell(arcjail_user.player, reason)
        return


@OnClientDisconnect
def listener_on_client_disconnect(index):
    if current_sweepstakes is None:
        return

    if index not in current_sweepstakes:
        return

    del current_sweepstakes[index]
