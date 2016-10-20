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

"""
This module fixes consequences of server crashes.
Since items are saved/deleted in the database immediately, while ArcjailUser's
are only saved on their disconnection / round end, there might be the case
where either:
a) Item was removed from the database, but is still referenced in ArcjailUser
b) Item was created in the database, but is yet to be referenced in ArcjailUser
"""

import json

from ...internal_events import InternalEvent
from ...models.arcjail_user import ArcjailUser as DB_ArcjailUser
from ...models.item import Item as DB_Item
from ...resource.logger import logger
from ...resource.sqlalchemy import Session


def repair():
    logger.log_debug("ArcJail: Database maintenance")

    db_session = Session()

    # Fix old references to deleted items
    logger.log_debug("Step 1/2...")
    for db_arcjail_user in db_session.query(DB_ArcjailUser).all():
        slot_data = json.loads(db_arcjail_user.slot_data)
        new_slot_data = []

        for item_id in slot_data:
            db_item = db_session.query(DB_Item).filter_by(id=item_id).first()
            if db_item is not None:
                new_slot_data.append(item_id)
            else:
                logger.log_debug("[!] User '{}' has invalid item '{}'".format(
                    db_arcjail_user.id, item_id))

        db_arcjail_user.slot_data = json.dumps(new_slot_data)

    # Fix missing references to newly obtained items
    # Also remove items that belong to deleted players
    logger.log_debug("Step 2/2...")
    for db_item in db_session.query(DB_Item).all():
        db_arcjail_user = db_session.query(DB_ArcjailUser).filter_by(
            steamid=db_item.current_owner).first()

        if db_arcjail_user is None:
            logger.log_debug(
                "[!] Item '{}' belongs to invalid user".format(db_item.id))

            db_session.delete(db_item)
            continue

        slot_data = json.loads(db_arcjail_user.slot_data)
        if db_item.id not in slot_data:
            logger.log_debug(
                "[!] User '{}' did not have item '{}' "
                "that belongs to him".format(db_arcjail_user.id, db_item.id))

            slot_data.append(db_item.id)
            db_arcjail_user.slot_data = json.dumps(slot_data)

    db_session.commit()
    db_session.close()

    logger.log_debug("ArcJail: End of database maintenance")


@InternalEvent('load')
def on_load():
    repair()
