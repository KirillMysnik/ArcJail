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

from stringtables.downloads import Downloadables

import arc_death_tools

from .internal_events import InternalEvent
from .resource.paths import DOWNLOADLISTS_PATH


def load_downloadables(file_name):
    file_path = DOWNLOADLISTS_PATH / file_name
    downloadables = Downloadables()

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            downloadables.add(line)

    return downloadables


def load():
    InternalEvent.fire('load')


def unload():
    InternalEvent.fire('unload')


from . import modules

from . import models
from .resource.sqlalchemy import Base, engine
Base.metadata.create_all(engine)
