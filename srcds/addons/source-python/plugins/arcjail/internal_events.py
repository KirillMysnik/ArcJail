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

from traceback import format_exc

from core import echo_console


class InternalEventManager(dict):
    def register_event_handler(self, event_name, handler):
        if event_name not in self:
            self[event_name] = []

        if handler in self[event_name]:
            raise ValueError("Handler {} is already registered to "
                             "handle '{}'".format(handler, event_name))

        self[event_name].append(handler)

    def unregister_event_handler(self, event_name, handler):
        if event_name not in self:
            raise KeyError("No '{}' event handlers are registered".format(
                event_name))

        self[event_name].remove(handler)

        if not self[event_name]:
            del self[event_name]

    def fire(self, event_name, event_var):
        exceptions = []
        for handler in self.get(event_name, ()):
            try:
                handler(**event_var)
            except Exception as e:
                exceptions.append(e)
                echo_console(format_exc())

        if exceptions:
            echo_console("{} exceptions were raised during handling of "
                         "'{}' event".format(len(exceptions), event_name))

internal_event_manager = InternalEventManager()


class InternalEventBase:
    manager = None

    def __init__(self, event_name):
        self.event_name = event_name

    def __call__(self, handler):
        self.register(handler)

    def register(self, handler):
        self.manager.register_event_handler(self.event_name, handler)

    def unregister(self, handler):
        self.manager.unregister_event_handler(self.event_name, handler)

    @classmethod
    def fire(cls, event_name, **event_var):
        cls.manager.fire(event_name, event_var)


class InternalEvent(InternalEventBase):
    manager = internal_event_manager
