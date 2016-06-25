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

from commands.server import ServerCommand
from core import echo_console
from events import Event
from listeners.tick import GameThread

from ...arcjail import InternalEvent

from ...classes.base_player_manager import BasePlayerManager

from ...models.arcjail_user import ArcjailUser as DB_ArcjailUser

from ...resource.sqlalchemy import Session

from .global_inventory import global_inventory

from .item import Item


class ArcjailUser:
    def __init__(self, player):
        self.player = player

        self.account = 0
        self.slot_data = []

        self._loaded = False

    @property
    def loaded(self):
        return self._loaded

    def load_from_database(self):
        if self.player.steamid == "BOT":
            return

        db_session = Session()

        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=self.player.steamid).first()

        if db_arcjail_user is not None:
            self.account = db_arcjail_user.account
            self.slot_data = loads(db_arcjail_user.slot_data)

        self._loaded = True

        db_session.close()

        # Iter over all of our items to initialize them in global_inventory
        list(self.iter_all_items())

    def save_to_database(self):
        if self.player.steamid == "BOT":
            return

        if not self._loaded:
            raise RuntimeError("User couldn't be synced with database")

        db_session = Session()

        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=self.player.steamid).first()

        if db_arcjail_user is None:
            db_arcjail_user = DB_ArcjailUser()
            db_arcjail_user.steamid = self.player.steamid
            db_session.add(db_arcjail_user)

        db_arcjail_user.account = self.account
        db_arcjail_user.slot_data = dumps(self.slot_data)

        db_session.commit()
        db_session.close()

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

        else:
            class_id, instance_id = args[:2]
            item = self.get_item_by_instance_id(class_id, instance_id)

        if item is None:
            if async:
                def create_item():
                    item = Item.create(class_id, instance_id, self.player,
                                       amount, async=False)

                    self.slot_data.append(item.id)

                GameThread(target=create_item).start()
                return None

            else:
                item = Item.create(
                    class_id, instance_id, self.player, amount, async=False)

                self.slot_data.append(item.id)
                return item

        item.give(amount, async)
        return item

    def take_item(self, *args, amount=1, async=True):
        if isinstance(args[0], Item):
            item = args[0]

        else:
            class_id, instance_id = args[:2]
            item = self.get_item_by_instance_id(class_id, instance_id)

        if item is None:
            raise ValueError(
                "Player {} doesn't have item (class_id={}, "
                "instance_id={})".format(self, class_id, instance_id))

        if item.amount - amount <= 0:
            self.slot_data.remove(item.id)

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


@ServerCommand('arcjail_add_credits')
def server_arcjail_add_credits(command):
    try:
        userid = command[1]
        credits = command[2]
    except IndexError:
        echo_console("Usage: arcjail_add_credits <userid> <credits>")
        return

    try:
        userid = int(userid)
    except ValueError:
        echo_console("Error: userid should be an integer")
        return

    try:
        credits = int(credits)
    except ValueError:
        echo_console("Error: credits should be an integer")
        return

    try:
        arcjail_user = arcjail_user_manager.get_by_userid(userid)
        if arcjail_user is None:
            raise KeyError
    except (KeyError, OverflowError, ValueError):
        echo_console("Couldn't find ArcjailUser (userid={})".format(userid))
        return

    arcjail_user.account += credits
    echo_console("Added {} credits to {}'s account".format(
        credits, arcjail_user.player.name))
