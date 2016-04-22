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

from events import Event
from events.custom import CustomEvent
from events.manager import game_event_manager
from events.resource import ResourceFile
from events.variable import BoolVariable, ShortVariable, StringVariable


__all__ = ['fake_death']


class Custom_Player_Death(CustomEvent):
    attacker = ShortVariable("The userid of the killer.")
    dominated = ShortVariable("True (1) if the kill caused the killer to be dominating the victim.")
    headshot = BoolVariable("True if the killshot was to the victim's head hitbox.")
    revenge = ShortVariable("True (1) if the victim was dominating the killer.")
    userid = ShortVariable("The userid of the victim.")
    weapon = StringVariable("The type of weapon used to kill the victim.")


class Player_Death_Fake(Custom_Player_Death):
    pass


class Player_Death_Real(Custom_Player_Death):
    pass


res_file = ResourceFile('arc_death_tools', 
                        Player_Death_Fake,
                        Player_Death_Real)
res_file.write()
res_file.load_events()


def _fake_death(attacker, dominated, headshot, revenge, userid, weapon):
    event = game_event_manager.create_event('player_death', True)
    event.set_int('attacker', attacker)
    event.set_int('dominated', dominated)
    event.set_bool('headshot', headshot)
    event.set_int('revenge', revenge)
    event.set_int('userid', userid)
    event.set_string('weapon', weapon)
    game_event_manager.fire_event(event)


_faked_deaths = []
def fake_death(victim, killer=None, headshot=False, dominated=False, revenge=False, weapon="point_hurt"):
    userid = victim.userid
    attacker = killer.userid if killer is not None else 0
    _faked_deaths.append(userid)
    _fake_death(attacker, int(dominated), headshot, int(revenge), userid, weapon)
    _faked_deaths.remove(userid)


@Event('player_death')
def on_player_death(pd_event):
    userid = pd_event.get_int('userid')
    
    if userid in _faked_deaths:
        new_pd_event = Player_Death_Fake()
    else:
        new_pd_event = Player_Death_Real()
    
    new_pd_event.attacker = pd_event.get_int('attacker')
    new_pd_event.dominated = pd_event.get_int('dominated')
    new_pd_event.headshot = pd_event.get_bool('headshot')
    new_pd_event.revenge = pd_event.get_int('revenge')
    new_pd_event.userid = userid
    new_pd_event.weapon = pd_event.get_string('weapon')
    
    new_pd_event.fire()