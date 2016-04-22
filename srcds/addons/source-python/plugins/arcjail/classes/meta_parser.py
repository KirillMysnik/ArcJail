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

def _find(src, start, end, ignorecase=True):
    if ignorecase:
        src_ = src.lower()
        start = start.lower()
        end = end.lower()

    else:
        src_ = src

    i1 = src_.find(start) + len(start)
    i2 = src_[i1:].find(end) + i1

    if start not in src_ or end not in src_[i1:]:
        return None

    return src[i1:i2]


class MetaParser:
    def __init__(self, raw):
        self.raw = raw

    def __getitem__(self, item):
        rs = _find(self.raw, '[%s]' % item, '[/%s]' % item, ignorecase=True)
        return rs.strip() if rs is not None else None


__all__ = ('MetaParser', )
