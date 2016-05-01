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

from .. import strings_module

from ...players import tell

from ...teams import GUARDS_TEAM, PRISONERS_TEAM


class BaseItem:
    id = None
    caption = None
    description = None
    icon = "base.png"
    max_per_slot = 1
    manual_activation = False
    auto_activation = False
    team_restriction = (GUARDS_TEAM, PRISONERS_TEAM)
    max_sold_per_round = -1
    price = 0

    def __init__(self, player, amount=1):
        self.player = player
        self.amount = amount

    def activate(self):
        tell(self.player, strings_module['activated'].tokenize(
            item=self.caption, left=self.amount))

    def load_json(self, item_json):
        self.amount = item_json['amount']

    def dump_json(self):
        return {
            'id': self.id,
            'amount': self.amount,
        }

    @classmethod
    def stat_max_per_slot(cls):
        if cls.max_per_slot > -1:
            return strings_module['item_stat max_per_slot'].tokenize(
                max_per_slot=cls.max_per_slot)
        return None

    @classmethod
    def stat_team_restriction(cls):
        if GUARDS_TEAM not in cls.team_restriction:
            return strings_module['team_restriction prisoners']
        elif PRISONERS_TEAM not in cls.team_restriction:
            return strings_module['team_restriction guards']
        return None

    @classmethod
    def stat_manual_activation(cls):
        if cls.manual_activation:
            return strings_module['item_stat manual_activation']
        return None

    @classmethod
    def stat_auto_activation(cls):
        if cls.auto_activation:
            return strings_module['item_stat auto_activation']
        return None

    @classmethod
    def stat_max_sold_per_round(cls):
        if cls.max_sold_per_round > -1:
            return strings_module['item_stat max_sold_per_round'].tokenize(
                max_sold_per_round=cls.max_sold_per_round)
        return None

    @classmethod
    def stat_price(cls):
        return strings_module['item_stat price'].tokenize(price=cls.price)
