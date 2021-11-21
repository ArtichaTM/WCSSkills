from contextlib import suppress

WCS_FOLDER = 'WCSSkills'

def load():
    # Main mod
    # Events
    from .events import custom_events
    # Admin
    from .admin import admin_events
    # WCS_Player
    from . import wcs
    # Databases
    from .db import wcs, admin
    # Commands
    from .commands import chat
    # Radio menu
    from .menus import wcs
    # XP
    from .other_functions import xp
    # Skills
    from .skills import immune, skill

    # Logging plugin load
    from WCSSkills.WCS_Logger import wcs_logger

    # Downloadables
    from stringtables.downloads import Downloadables
    # Sounds
    Downloadables().add_directory(f'sound/{WCS_FOLDER}/')

    wcs_logger('info', 'Plugin loaded successfully')

def unload():

    # Unloading players
    from WCSSkills.wcs.WCSP.wcsplayer import WCS_Players as WCSP
    for player in WCSP.values():
        with suppress(AttributeError):
            player.unload_instance()

    # Unloading Databases and JSONs
    from WCSSkills.db.wcs import DB_users
    from WCSSkills.db.admin import DB_admin, DC_history
    DB_users.unload_instance()
    DB_admin.unload_instance()
    DC_history.unload_instance()

    # Logging plugin unload
    from WCSSkills.WCS_Logger import wcs_logger
    wcs_logger('info','Plugin unloaded successfully')

    # Unloading wcs_logger
    wcs_logger.unload_instance()