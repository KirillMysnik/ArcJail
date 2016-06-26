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

from ...resource.strings import build_module_strings

from ..players import tell

from ..teams import GUARDS_TEAM, PRISONERS_TEAM


strings_module = build_module_strings('arcjail/item_instance')


class BaseItemInstance(dict):
    manual_activation = False
    auto_activation = False
    team_restriction = (GUARDS_TEAM, PRISONERS_TEAM)
    use_team_restriction = (GUARDS_TEAM, PRISONERS_TEAM)

    def __init__(self, class_id, instance_id, instance_config, category_id):
        super().__init__()

        self._strings_class = build_module_strings(
            'arcjail/items/{}'.format(class_id))

        self.class_id = class_id
        self.instance_id = instance_id
        self.update(instance_config)
        self.category_id = category_id

    @property
    def caption(self):
        return self._strings_class[self['caption']]

    @property
    def description(self):
        return self._strings_class[self['description']]

    @property
    def stat_max_per_slot(self):
        if self.get('max_per_slot', -1) > -1:
            return strings_module['item_stat max_per_slot'].tokenize(
                max_per_slot=self['max_per_slot'])
        return None

    @property
    def stat_team_restriction(self):
        if GUARDS_TEAM not in self.team_restriction:
            return strings_module['team_restriction prisoners']
        elif PRISONERS_TEAM not in self.team_restriction:
            return strings_module['team_restriction guards']
        return None

    @property
    def stat_manual_activation(self):
        if self.manual_activation:
            return strings_module['item_stat manual_activation']
        return None

    @property
    def stat_auto_activation(self):
        if self.auto_activation:
            return strings_module['item_stat auto_activation']
        return None

    @property
    def stat_max_sold_per_round(self):
        if self.get('max_sold_per_round', -1) > -1:
            return strings_module['item_stat max_sold_per_round'].tokenize(
                max_sold_per_round=self['max_sold_per_round'])
        return None

    @property
    def stat_price(self):
        return strings_module['item_stat price'].tokenize(price=self['price'])

    def get_purchase_denial_reason(self, player, amount):
        return None

    def try_activate(self, player, amount, async=True):
        tell(player, strings_module['activated'].tokenize(
            item=self.caption, left=amount))

        return None
