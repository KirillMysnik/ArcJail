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

def value_from_string(val, type_, default=None):
    type_ = type_.lower()

    if type_ == 'str':
        return val

    if type_ == 'int':
        try:
            return int(val)

        except ValueError:
            return default

    if type_ == 'float':
        try:
            return float(val)

        except ValueError:
            return default

    if type_ == 'bool':
        return val.lower() not in ('no', 'off', 'false', '0', '0.0')

    if type_ == 'tuple':
        if ',' in val:
            return tuple(map(lambda item: item.strip(), val.split(',')))

        if ' ' in val:
            return tuple(val.split())

        return (val, )

    raise TypeError("Unknown value type: %s" % type_)


def value_to_string(val):
    if hasattr(val, '__iter__'):
        if isinstance(val, str):
            return val
        return ','.join(map(str, val))

    if isinstance(val, bool):
        return "1" if val else "0"

    return str(val)
