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

from engines.precache import Model
from engines.sound import Attenuation, Sound
from entities.entity import Entity
from events import Event

from mathlib import Vector

from ....resource.strings import build_module_strings

from ..item_instance import BaseItemInstance

from . import register_item_instance_class


MAX_DISPOSED_PROPS_PER_ROUND = 10
MAX_TARGET_DISTANCE = 384
SPAWN_SOUND_PATH = "ambient/energy/whiteflash.wav"


strings_module = build_module_strings('arcjail/items/disposable_prop')
props_disposed = 0


class DisposableProp(BaseItemInstance):
    manual_activation = True

    def try_activate(self, player, amount):
        global props_disposed

        if props_disposed >= MAX_DISPOSED_PROPS_PER_ROUND:
            return strings_module['fail too_many']

        coords = player.get_view_coordinates()
        if coords is None:
            return strings_module['fail wrong_place']

        if coords.get_distance(player.origin) > MAX_TARGET_DISTANCE:
            return strings_module['fail too_far']

        # TODO: Add game area check

        props_disposed += 1

        entity = Entity.create(self['entity_classname'])
        entity.model = Model(self['model_path'])
        entity.skin = randint(
            self.get('skin_min', 0), self.get('skin_max', 0))

        origin = coords + Vector(0, 0, self.get('z_offset', 0))
        entity.teleport(origin, None, None)

        entity.spawn()

        Sound(SPAWN_SOUND_PATH, index=entity.index,
              attenuation=Attenuation.STATIC).play()

        return super().try_activate(player, amount)

register_item_instance_class('disposable_prop', DisposableProp)


@Event('round_start')
def on_round_start(game_event):
    global props_disposed
    props_disposed = 0
