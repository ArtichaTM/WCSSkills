from contextlib import suppress

WCS_FOLDER = 'WCSSkills'

def load():
    import WCSSkills

def unload():

    # Unloading players
    from WCSSkills.wcs.wcsplayer import WCS_Players as WCSP
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
    from WCSSkills.other_functions.functions import wcs_logger
    wcs_logger('info','Plugin unloaded successfully')

    # Unloading wcs_logger
    wcs_logger.unload_instance()