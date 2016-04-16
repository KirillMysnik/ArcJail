from cvars.flags import ConVarFlags


def silent_set(cvar, type_, value):
    if cvar.is_flag_set(ConVarFlags.NOTIFY):
        cvar.remove_flags(ConVarFlags.NOTIFY)
        getattr(cvar, 'set_{}'.format(type_))(value)
        cvar.add_flags(ConVarFlags.NOTIFY)

    else:
        getattr(cvar, 'set_{}'.format(type_))(value)
