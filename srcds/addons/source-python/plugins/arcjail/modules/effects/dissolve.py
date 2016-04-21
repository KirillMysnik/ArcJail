from core import PLATFORM
from engines.server import global_vars
from memory import Convention, DataType, find_binary, NULL


if PLATFORM == 'windows':
    DISSOLVE_IDENTIFIER = b'\x55\x8B\xEC\x80\x7D\x10\x00\x56\x57\x8B\xF1\x74\x14'
else:
    DISSOLVE_IDENTIFIER = None

server = find_binary('server')

DISSOLVE = server[DISSOLVE_IDENTIFIER].make_function(
    Convention.THISCALL,
    (
        DataType.POINTER,
        DataType.POINTER,
        DataType.FLOAT,
        DataType.BOOL,
        DataType.INT,
        DataType.POINTER,
        DataType.INT
    ),
    DataType.BOOL
)


def dissolve(entity, type_=0):
    DISSOLVE(
        entity.pointer, NULL,
        global_vars.current_time,
        False, type_, entity.origin, 2
    )
