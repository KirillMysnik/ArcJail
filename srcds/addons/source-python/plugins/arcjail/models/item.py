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

from sqlalchemy import Column, Integer, String

from ..resource.config import config
from ..resource.sqlalchemy import Base


class Item(Base):
    __tablename__ = config['database']['prefix'] + "items"

    id = Column(Integer, primary_key=True)
    current_owner = Column(String(32))

    class_id = Column(String(32))
    instance_id = Column(String(32))
    amount = Column(Integer)

    def __repr__(self):
        return "<Item({})>".format(self.id)
