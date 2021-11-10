# ../MapChanger.py

from engines.server import server, queue_command_string

def load():
    from .HUD import HUD


def unload():
    from . import counter
    from . import HUD
    HUD.HUD.unload_instance()