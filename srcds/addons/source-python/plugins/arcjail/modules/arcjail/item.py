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

from players.helpers import index_from_steamid

from ...models.item import Item as DB_Item

from ...resource.logger import logger

from ...resource.sqlalchemy import Session

from ..players import main_player_manager

from .item_classes import item_classes


class Item:
    def __init__(self, id_):
        self.id = id_
        self._current_owner = ""
        self.class_id = None
        self.instance_id = None
        self.amount = 0

        self._loaded = False

    @property
    def class_(self):
        return item_classes[self.class_id][self.instance_id]

    def get_player(self):
        if self._current_owner:
            return main_player_manager[index_from_steamid(self._current_owner)]

        return None

    def set_player(self, player):
        if player is None:
            self._current_owner = ""
        else:
            self._current_owner = player.steamid

    player = property(get_player, set_player)

    @property
    def loaded(self):
        return self._loaded

    def load_from_database(self):
        db_session = Session()

        db_item = db_session.query(DB_Item).filter_by(id=self.id).first()
        if db_item is None:
            db_session.close()

            msg = "Item (id={}) does not exist in the database".format(self.id)
            logger.log_warning(msg)
            raise KeyError(msg)

        self._current_owner = db_item.current_owner
        self.class_id = db_item.class_id
        self.instance_id = db_item.instance_id
        self.amount = db_item.amount

        self._loaded = True

        db_session.close()

    def save_to_database(self):
        if not self._loaded:
            msg = "Item {} couldn't be synced with database".format(self)
            logger.log_warning(msg)
            raise RuntimeError(msg)

        db_session = Session()

        db_item = db_session.query(DB_Item).filter_by(id=self.id).first()

        if db_item is None:
            db_item = DB_Item()
            db_session.add(db_item)

        db_item.current_owner = self._current_owner
        db_item.class_id = self.class_id
        db_item.instance_id = self.instance_id
        db_item.amount = self.amount

        db_session.commit()

        self.id = db_item.id

        db_session.close()

    def delete_from_database(self):
        db_session = Session()

        db_item = db_session.query(DB_Item).filter_by(id=self.id).first()
        if db_item is None:
            db_session.close()

            msg = "Item (id={}) does not exist in the database".format(self.id)
            logger.log_warning(msg)
            raise KeyError(msg)

        db_session.delete(db_item)

        self.id = None
        self._loaded = False

        db_session.commit()
        db_session.close()

    @staticmethod
    def delete(item, async=True):
        from .global_inventory import global_inventory

        global_inventory.delete(item, async)

    @staticmethod
    def create(class_id, instance_id, player=None, amount=1, async=True):
        from .global_inventory import global_inventory

        return global_inventory.create(
            class_id, instance_id, player, amount, async)

    def take(self, amount, async=True):
        if amount > self.amount:
            msg = ("Can't take {} pieces of item {}: player only "
                   "has {}".format(amount, self, self.amount))

            logger.log_warning(msg)
            raise ValueError(msg)

        self.amount -= amount

        if not self.amount:
            Item.delete(self, async)

    def give(self, amount, async=True):
        self.amount += amount

    def __str__(self):
        return "<Item(id={}, class_id={}, instance_id={})>".format(
            self.id, self.class_.class_id, self.class_.instance_id)
