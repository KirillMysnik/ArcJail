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


class CallbackDecorator:
    def __init__(self, callback):
        self.callback = callback
        self.register()

    def __call__(self, *args, **kwargs):
        self.callback(*args, **kwargs)

    def register(self):
        raise NotImplementedError

    def unregister(self):
        raise NotImplementedError
