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

from spam_proof_commands.client import ClientCommand
from spam_proof_commands.say import SayCommand

from players.entity import Player

from .motd.inventory import send_page


ANTI_SPAM_TIMEOUT = 2


@ClientCommand(ANTI_SPAM_TIMEOUT, ['inventory', 'inv'])
@SayCommand(ANTI_SPAM_TIMEOUT, ['!inventory', '!inv'])
def command_inventory(command, index, team_only=None):
    send_page(Player(index))
