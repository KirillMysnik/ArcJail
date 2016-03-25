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
