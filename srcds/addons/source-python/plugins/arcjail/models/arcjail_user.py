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

from sqlalchemy import Column, Integer, String, Text

from ..resource.config import config
from ..resource.sqlalchemy import Base


class ArcjailUser(Base):
    __tablename__ = config['database']['prefix'] + "arcjail_users"

    id = Column(Integer, primary_key=True)
    steamid = Column(String(32))

    last_seen = Column(Integer)
    last_used_name = Column(String(32))
    last_online_reward = Column(Integer)
    account = Column(Integer)
    slot_data = Column(Text)

    def __repr__(self):
        return "<ArcjailUser({})>".format(self.id)
