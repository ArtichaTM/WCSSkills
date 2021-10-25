from contextlib import suppress

WCS_FOLDER = 'WCSSkills'

def load():
    global WCSSkills
    import WCSSkills
    WCSSkills.wcs_logger('info', 'Plugin loaded successfully')

def unload():

    # Unloading players
    for player in WCSSkills.wcs.wcsplayer.WCS_Players.values():
        with suppress(AttributeError):
            player.unload_instance()

    # Unloading Databases and JSONs
    WCSSkills.db.wcs.DB_users.unload_instance()
    WCSSkills.db.admin.DB_admin.unload_instance()
    WCSSkills.db.admin.DC_history.unload_instance()

    # Logging plugin unload
    WCSSkills.other_functions.functions.wcs_logger(
        'info','Plugin unloaded successfully')

    # Unloading wcs_logger
    WCSSkills.other_functions.functions.wcs_logger.unload_instance()