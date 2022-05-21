from contextlib import suppress

WCS_FOLDER = 'WCSSkills'

def load():
    from .WCS_Logger import wcs_logger
    wcs_logger('info', 'Plugin is loading')
    # Main mod
    # Events
    from .events import custom_events
    # other_functions
    from . import other_functions
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
    # Skills
    from .skills import immune, skill

    # Downloadables
    from stringtables.downloads import Downloadables
    downloads = Downloadables() # Instance
    downloads.add_directory(f'sound/{WCS_FOLDER}/') # Adding sounds to download list
    downloads.add_directory(f'materials/models/{WCS_FOLDER}/') # Adding materials download list
    downloads.add_directory(f'models/{WCS_FOLDER}/') # Adding models download list

    wcs_logger('info', 'Plugin loaded successfully')

def unload():

    # Making wcs_logger always close
    try:
        from .WCS_Logger import wcs_logger
        wcs_logger('info', 'Plugin is unloading')

        # Unloading players
        from .wcs.WCSP.wcsplayer import WCS_Players as WCSP
        for player in WCSP.values():
            with suppress(AttributeError):
                player.unload_instance()

        # Unloading Databases and JSONs
        from .db.wcs import DB_users
        from .db.admin import DB_admin, DC_history
        DB_users.unload_instance()
        DB_admin.unload_instance()
        DC_history.unload_instance()

        # Logging plugin unload
        wcs_logger('info','Plugin unloaded successfully')

    finally:
        # CLosing wcs_logger

        # Unloading wcs_logger
        wcs_logger.unload_instance()