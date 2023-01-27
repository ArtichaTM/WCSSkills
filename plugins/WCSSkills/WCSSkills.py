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

    # Instance of wcs downloadables
    downloads = Downloadables()

    # Sounds folder
    try:
        downloads.add_directory(f'sound/{WCS_FOLDER}/')  # Adding sounds to download list
    except FileNotFoundError:
        wcs_logger('error', "Couldn't add sound folder to downloadables")

    # Materials
    try:
        downloads.add_directory(f'materials/models/{WCS_FOLDER}/')  # Adding sounds to download list
    except FileNotFoundError:
        wcs_logger('error', "Couldn't add materials folder to downloadables")

    # Models
    try:
        downloads.add_directory(f'models/{WCS_FOLDER}/')  # Adding sounds to download list
    except FileNotFoundError:
        wcs_logger('error', "Couldn't add models folder to downloadables")

    wcs_logger('info', 'Plugin loaded successfully')


def unload():

    from .WCS_Logger import wcs_logger
    wcs_logger('info', 'Plugin is unloading')

    # Making wcs_logger always close
    try:

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
        wcs_logger('info', 'Plugin unloaded successfully')

    finally:
        # CLosing wcs_logger

        # Unloading wcs_logger
        wcs_logger.unload_instance()
