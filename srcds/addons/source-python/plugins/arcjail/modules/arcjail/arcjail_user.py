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

from json import dumps, loads
from time import time

from events import Event
from listeners.tick import GameThread

from ...arcjail import InternalEvent

from ...classes.base_player_manager import BasePlayerManager

from ...models.arcjail_user import ArcjailUser as DB_ArcjailUser

from ...resource.logger import logger

from ...resource.sqlalchemy import Session

from .global_inventory import global_inventory

from .item import Item


class ArcjailUser:
    def __init__(self, player):
        self.player = player

        # We're saving to database asynchronously, and player.steamid will
        # be unavailable
        self._steamid = player.steamid

        self.last_online_reward = time()
        self.account = 0
        self.slot_data = []

        self._loaded = False

    @property
    def loaded(self):
        return self._loaded

    def load_from_database(self):
        if self._steamid == "BOT":
            return

        db_session = Session()

        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=self._steamid).first()

        if db_arcjail_user is not None:
            self.account = db_arcjail_user.account
            self.last_online_reward = db_arcjail_user.last_online_reward
            self.slot_data = loads(db_arcjail_user.slot_data)

        self._loaded = True

        db_session.close()

        # Iter over all of our items to initialize them in global_inventory
        list(self.iter_all_items())

    def save_to_database(self):
        from ..credits import credits_config

        if self._steamid == "BOT":
            return

        if not self._loaded:
            raise RuntimeError("User couldn't be synced with database")

        db_session = Session()

        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=self._steamid).first()

        if db_arcjail_user is None:
            self.account = credits_config['initial_credits']['initial_credits']

            db_arcjail_user = DB_ArcjailUser()
            db_arcjail_user.steamid = self._steamid
            db_session.add(db_arcjail_user)

        db_arcjail_user.last_seen = time()
        db_arcjail_user.last_used_name = self.player.name
        db_arcjail_user.last_online_reward = self.last_online_reward
        db_arcjail_user.account = self.account
        db_arcjail_user.slot_data = dumps(self.slot_data)

        db_session.commit()
        db_session.close()

        for item in self.iter_all_items():
            global_inventory.save(item, async=False)

    @classmethod
    def save_temp_item(cls, steamid, item):
        """Used to save items whose IDs became
        available after their owner has disconnected."""

        if steamid == "BOT":
            return

        db_session = Session()

        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=steamid).first()

        if db_arcjail_user is None:
            db_arcjail_user = DB_ArcjailUser()
            db_arcjail_user.steamid = steamid
            db_session.add(db_arcjail_user)

            slot_data = []

        else:
            slot_data = loads(db_arcjail_user.slot_data)

        db_arcjail_user.slot_data = dumps(slot_data + [item.id, ])

        db_session.commit()
        db_session.close()
    
    def iter_all_items(self):
        for item_id in self.slot_data:
            yield global_inventory[item_id]
    
    def iter_items_by_class_id(self, class_id):
        for item in self.iter_all_items():
            if item.class_.class_id == class_id:
                yield item
    
    def get_item_by_instance_id(self, class_id, instance_id):
        for item in self.iter_items_by_class_id(class_id):
            if item.class_.instance_id == instance_id:
                return item
        
        return None
    
    def give_item(self, *args, amount=1, async=True):
        if isinstance(args[0], Item):
            item = args[0]
            logger.log_debug(
                "ArcjailUser.give_item: Giving item {} to (SteamID={}) "
                "(async={})".format(item, self.player.steamid, async))

        else:
            class_id, instance_id = args[:2]
            logger.log_debug(
                "ArcjailUser.give_item: Giving item (class_id={}, "
                "instance_id={}) to (SteamID={}) (async={})".format(
                    class_id, instance_id, self.player.steamid, async))

            item = self.get_item_by_instance_id(class_id, instance_id)

        if item is None:
            if async:
                def create_item():
                    item = Item.create(class_id, instance_id, self.player,
                                       amount, async=False)

                    self.slot_data.append(item.id)
                    logger.log_debug(
                        "ArcjailUser.give_item: ... finished creating new "
                        "item {} (async=True) "
                        "-- ID added to slot data".format(item))

                logger.log_debug(
                    "ArcjailUser.give_item: Creating new item (class_id={}, "
                    "instance_id={}) to (SteamID={}) (async=True)...".format(
                        class_id, instance_id, self.player.steamid))

                GameThread(target=create_item).start()
                return None

            else:
                item = Item.create(
                    class_id, instance_id, self.player, amount, async=False)

                self.slot_data.append(item.id)

                logger.log_debug(
                    "ArcjailUser.give_item: Created new item {} to "
                    "(SteamID={}) (async=False) "
                    "-- ID added to slot data".format(
                        item, self.player.steamid))

                return item

        item.give(amount, async)
        return item

    def take_item(self, *args, amount=1, async=True):
        if isinstance(args[0], Item):
            item = args[0]
            logger.log_debug(
                "ArcjailUser.take_item: Taking item {} from (SteamID={}) "
                "(async={})".format(item, self.player.steamid, async))

        else:
            class_id, instance_id = args[:2]
            logger.log_debug(
                "ArcjailUser.take_item: Taking item (class_id={}, "
                "instance_id={}) from (SteamID={}) (async={})".format(
                    class_id, instance_id, self.player.steamid, async))

            item = self.get_item_by_instance_id(class_id, instance_id)

        if item is None:
            msg = ("Player {} doesn't have item (class_id={}, "
                   "instance_id={})".format(self, class_id, instance_id))

            logger.log_warning(msg)
            raise ValueError(msg)

        if item.amount - amount <= 0:
            self.slot_data.remove(item.id)
            logger.log_debug("ArcjailUser.take_item: "
                             "-- ID removed from slot data")

        item.take(amount, async)
        return item

    def __str__(self):
        return "<ArcjailUser(userid={})>".format(self.player.userid)


class ArcjailUserManager(BasePlayerManager):
    def create(self, player):
        self[player.index] = arcjail_user = self._base_class(player)

        GameThread(target=arcjail_user.load_from_database).start()

        for callback in self._callbacks_on_player_registered:
            callback(self[player.index])

        return self[player.index]

    def delete(self, player):
        arcjail_user = self[player.index]
        for callback in self._callbacks_on_player_unregistered:
            callback(arcjail_user)

        GameThread(target=arcjail_user.save_to_database).start()

        return self.pop(player.index)

arcjail_user_manager = ArcjailUserManager(base_class=ArcjailUser)


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']
    arcjail_user_manager.create(player)


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']
    arcjail_user_manager.delete(player)


@Event('round_end')
def on_round_end(game_event):
    for arcjail_user in arcjail_user_manager.values():
        GameThread(target=arcjail_user.save_to_database).start()


@InternalEvent('unload')
def on_unload(event_var):
    for arcjail_user in arcjail_user_manager.values():
        GameThread(target=arcjail_user.save_to_database).start()
