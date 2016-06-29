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

from datetime import datetime
from time import time

from listeners.tick import GameThread

from ..arcjail import InternalEvent

from ..resource.sqlalchemy import Session

from ..resource.strings import build_module_strings

from ..models.guards_license import GuardsLicense as DB_GuardsLicense

from .admin import section

from .players import tell


DEFAULT_LICENSE_DURATION = 7 * 24 * 3600
strings_module = build_module_strings('guards_license')


class GuardsLicense:
    def __init__(self):
        self.id = None
        self.issuer = None
        self.valid_from = 0
        self.valid_through = 0


class GuardsLicensesManager(dict):
    def has_license(self, player):
        license_ = self.get_license(player)
        if license_ is None:
            return False

        if license_.valid_through < time():
            return False

        return True

    def get_license(self, player):
        return self[player.index]

    def revoke_license(self, issuer, player):
        if not self.has_license(player):
            raise ValueError("SteamID '{}' doesn't have "
                             "a valid license".format(player.steamid))

        license_ = self.get_license(player)
        self[player.index] = None

        def save_revocation():
            db_session = Session()

            db_guards_license = db_session.query(DB_GuardsLicense).filter_by(
                id=license_.id).first()

            db_guards_license.revoked = True
            db_guards_license.revoked_by = issuer.steamid

            db_session.commit()
            db_session.close()

        GameThread(target=save_revocation).start()

    def give_license(self, issuer, player, duration):
        if self.has_license(player):
            raise ValueError("SteamID '{}' already has "
                             "a valid license".format(player.steamid))

        current_time = time()
        new_license_ = self[player.index] = GuardsLicense()
        new_license_.issuer = issuer.steamid
        new_license_.valid_from = current_time
        new_license_.valid_through = current_time + duration

        def save_new_license():
            db_session = Session()

            db_guards_license = DB_GuardsLicense()
            db_guards_license.steamid = player.steamid
            db_guards_license.issuer = issuer.steamid
            db_guards_license.valid_from = current_time
            db_guards_license.valid_through = current_time + duration
            db_guards_license.revoked = False
            db_guards_license.revoked_by = ""

            db_session.add(db_guards_license)
            db_session.commit()

            new_license_.id = db_guards_license.id
            db_session.close()

        GameThread(target=save_new_license).start()

    def load_license(self, player):
        db_session = Session()

        db_guards_license = db_session.query(DB_GuardsLicense).\
            filter_by(steamid=player.steamid).\
            filter_by(revoked=False).\
            order_by(DB_GuardsLicense.valid_through.desc()).first()

        if db_guards_license is None:
            db_session.close()
            return

        license_ = self[player.index] = GuardsLicense()
        license_.id = db_guards_license.id
        license_.issuer = db_guards_license.issuer
        license_.valid_from = db_guards_license.valid_from
        license_.valid_through = db_guards_license.valid_through

        db_session.close()

guards_licenses_manager = GuardsLicensesManager()


def format_ts(ts):
    return datetime.fromtimestamp(ts).strftime('%d.%m.%Y %H:%M:%S')


@InternalEvent('main_player_created')
def on_main_player_created(event_var):
    player = event_var['main_player']

    guards_licenses_manager[player.index] = None

    GameThread(
        target=guards_licenses_manager.load_license, args=(player, )).start()


@InternalEvent('main_player_deleted')
def on_main_player_deleted(event_var):
    player = event_var['main_player']

    del guards_licenses_manager[player.index]


# =============================================================================
# >> ARCADMIN ENTRIES
# =============================================================================
if section is not None:
    from arcadmin.classes.menu import PlayerBasedCommand, Section

    class ViewLicense(PlayerBasedCommand):
        base_filter = 'human'
        include_equal_priorities = True

        def filter(self, admin, player):
            if not super().filter(admin, player):
                return False

            return guards_licenses_manager.has_license(player)

        @staticmethod
        def player_select_callback(admin, players):
            for player in players:
                license_ = guards_licenses_manager.get_license(player)
                tell(
                    admin.player,
                    strings_module['arcadmin license_info'].tokenize(
                        player=player.name,
                        valid_from=format_ts(license_.valid_from),
                        valid_through=format_ts(license_.valid_through),
                    )
                )

    license_section = section.add_child(
        Section, strings_module['arcadmin section'])

    license_section.add_child(
        ViewLicense, strings_module['arcadmin option view_license'],
        'jail.guards_license.view', 'view'
    )

    class GiveLicense(PlayerBasedCommand):
        base_filter = 'human'
        include_equal_priorities = True

        def filter(self, admin, player):
            if not super().filter(admin, player):
                return False

            return not guards_licenses_manager.has_license(player)

        @staticmethod
        def player_select_callback(admin, players):
            for player in players:
                guards_licenses_manager.give_license(
                    admin.player, player, DEFAULT_LICENSE_DURATION)

                admin.announce(
                    strings_module['arcadmin license_given'].tokenize(
                        player=player.name))

    license_section.add_child(
        GiveLicense, strings_module['arcadmin option give_license'],
        'jail.guards_license.give', 'give'
    )

    class RevokeLicense(PlayerBasedCommand):
        base_filter = 'human'
        include_equal_priorities = False

        def filter(self, admin, player):
            if not super().filter(admin, player):
                return False

            if not guards_licenses_manager.has_license(player):
                return False

            # Licenses that were just given may not have ID from database yet
            license_ = guards_licenses_manager.get_license(player)
            if license_.id is None:
                return False

            return True

        @staticmethod
        def player_select_callback(admin, players):
            for player in players:
                guards_licenses_manager.revoke_license(admin.player, player)

                admin.announce(
                    strings_module['arcadmin license_revoked'].tokenize(
                        player=player.name))

    license_section.add_child(
        RevokeLicense, strings_module['arcadmin option revoke_license'],
        'jail.guards_license.revoke', 'revoke'
    )