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
