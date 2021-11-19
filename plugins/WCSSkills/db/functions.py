# ../db/functions.py
""" This file stores functions for databases """
# =============================================================================
# >> Imports
# =============================================================================
# Source.Python Imports
from players.helpers import index_from_steamid
from players.entity import Player

# =============================================================================
# >> Functions/Classes
# =============================================================================
class db_cursor:
    """ Class that realizes work with cursor """

    def __init__(self, db):
        self._cur = db.cursor()

    def __enter__(self):
        return self._cur

    def __exit__(self, *args):
        self._cur.close()

class Disconnected_user:
    """ Class that stores name, steamid and address of user """
    __slots__ = ('is_player', 'name', 'steamid', 'address')

    def __init__(self, name, steamid, ip):
        self.is_player = False
        self.name = name
        self.steamid = steamid
        self.address = ip

    @classmethod
    def create(cls, name, steamid, ip):
        try: index = index_from_steamid(steamid)
        except ValueError:
            instance = cls(name, steamid, ip)
            return instance
        else: return Player(index)

    def kick(self, reason): pass