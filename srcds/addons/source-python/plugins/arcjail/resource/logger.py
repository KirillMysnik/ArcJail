from datetime import date
from logging import DEBUG

from cvars import ConVar
from loggers import LogManager, SCRIPT_LOG


cvar_level = ConVar(
    "arcjail_logging_level", str(DEBUG), "ArcJail logging level")

cvar_areas = ConVar(
    "arcjail_logging_level", str(SCRIPT_LOG), "ArcJail logging areas")

logger = LogManager(
    'arcjail_logger', cvar_level, cvar_areas,
    "arcjail/arcjail-{}".format(date.today().strftime('%Y-%m-%d')),
    '%(asctime)s - %(levelname)s\n\t%(message)s\n\n',
    '%Y-%m-%d %H:%M:%S'
)
