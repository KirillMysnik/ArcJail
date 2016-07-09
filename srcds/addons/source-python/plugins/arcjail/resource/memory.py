from core import GAME_NAME
from memory.manager import TypeManager

from .paths import ARCJAIL_DATA_PATH


manager = TypeManager()

CCSPlayer = manager.create_type_from_file(
    'CCSPlayer',
    ARCJAIL_DATA_PATH / 'memory' / GAME_NAME / 'CCSPlayer.ini'
)
