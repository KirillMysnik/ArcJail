_enabled = 0


def enable():
    global _enabled
    _enabled += 1


def disable():
    global _enabled
    _enabled = max(0, _enabled - 1)
