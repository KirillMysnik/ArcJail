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

from filters.players import PlayerIter


from ..arcjail import InternalEvent


PRISONERS_TEAM = 2
GUARDS_TEAM = 3


@InternalEvent('load')
def on_load(event_var):
    is_prisoner = lambda player: player.team == PRISONERS_TEAM
    is_guard = lambda player: player.team == GUARDS_TEAM

    PlayerIter.register_filter('jail_prisoner', is_prisoner)
    PlayerIter.register_filter('jail_guard', is_guard)


@InternalEvent('unload')
def on_unload(event_var):
    PlayerIter.unregister_filter('jail_prisoner')
    PlayerIter.unregister_filter('jail_guard')
