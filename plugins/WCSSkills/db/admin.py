# ../WCSSkills/db/wcs.py
# =============================================================================
# >> IMPORTS
# =============================================================================

# Python Imports
# Database
import sqlite3
# Json loader
from json import loads, dump
from json.decoder import JSONDecodeError
# Python paths
from os.path import isfile
# Time
from time import time

# Source.Python Imports
from listeners.tick import Repeat

# Plugin Imports
from .functions import db_cursor
# Constants
from WCSSkills.other_functions.constants import PATH_DATABASE_ADMIN
from WCSSkills.other_functions.constants import PATH_JSON_DISCONNECTED_PLAYERS
from WCSSkills.admin.constants import Punishment_types
from WCSSkills.admin.constants import amount_of_players_in_history as history_count
# Logger
from WCSSkills.other_functions.functions import wcs_logger
# Punishment expire event
from WCSSkills.admin.admin_custom_events import Punishment_expired

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('DB_admin',
           'DC_history')


# =============================================================================
# >> Classes
# =============================================================================
class _DB_admin:
    """
    Class saves all punished players
    """
    __slots__ = ('db', 'repeat')

    def __init__(self, path_to_db):
        """
        :param path_to_db str
            Where must be located db. Absolute path
        """

        # Connecting db
        self.db = sqlite3.connect(path_to_db)

        # Setting Pragmas
        with db_cursor(self.db) as cur:
            cur.execute('PRAGMA main.synchronous = NORMAL')
            cur.execute('PRAGMA main.journal_mode = OFF')
            cur.execute('PRAGMA temp_store = MEMORY')

        with db_cursor(self.db) as cur:

            # Checking for tables in DB
            cur.execute(f"SELECT name FROM sqlite_master WHERE type = 'table'")
            tables = [table[0] for table in cur.fetchall()]

            # Next if-s created to check if any table doesn't exist
            if 'permanent' not in tables:
                cur.execute(f"""CREATE TABLE 'permanent'
                    (
                    date INTEGER NOT NULL,
                    type INT NOT NULL,
                    vname TEXT,
                    vsteamid TEXT,
                    vip TEXT,
                    aname TEXT,
                    asteamid TEXT,
                    reason INT
                    )"""
                            )
                wcs_logger('warning db', f"No DB_admin 'permanent' found. "
                              f"New DB file is created without any entry")

            if 'active' not in tables:
                cur.execute(f"""CREATE TABLE 'active'
                    (
                    date INTEGER NOT NULL,
                    type INTEGER NOT NULL,
                    vname TEXT,
                    vsteamid TEXT,
                    vip TEXT,
                    aname TEXT,
                    asteamid TEXT,
                    reason INT,
                    duration INTEGER NOT NULL
                    )"""
                            )
                wcs_logger('warning db', f"No DB_admin 'active' found. "
                              f"New DB file is created without any entry")

            if 'history' not in tables:
                cur.execute(f"""CREATE TABLE 'history'
                    (
                    date INTEGER NOT NULL,
                    type INTEGER NOT NULL,
                    vname TEXT,
                    vsteamid TEXT,
                    vip TEXT,
                    aname TEXT,
                    asteamid TEXT,
                    reason INT,
                    duration INTEGER,
                    expire_time INTEGER
                    )"""
                            )
                wcs_logger('warning db', f"No DB_admin 'history' found. "
                              f"New DB file is created without any entry")

            if 'once' not in tables:
                cur.execute(f"""CREATE TABLE 'once'
                    (
                    date INTEGER NOT NULL,
                    type INTEGER NOT NULL,
                    vname TEXT,
                    vsteamid TEXT,
                    vip TEXT,
                    aname TEXT,
                    asteamid TEXT,
                    reason INT
                    )"""
                            )
                wcs_logger('warning db', f"No DB_admin 'once' found. "
                              f"New DB file is created without any entry")


            # Setting Pragmas
            cur.execute('PRAGMA main.synchronous = FULL')
            cur.execute('PRAGMA main.journal_mode = TRUNCATE')
            cur.execute('PRAGMA temp_store = MEMORY')

            self.db.commit()

        # Repeat to look after expired punishments
        self.repeat = Repeat(self._update_active)
        self.repeat.start(30, execute_on_start = True)

    def add_entry(self,
                ptype: int,
                victim_name: str,
                victim_steamid: str,
                victim_ip: str,
                admin_name: str,
                admin_steamid: str,
                reason: str,
                duration: int = -1) -> None:

        """
        Adding new punishment to the database

        :param int ptype:
            Punishment_Types type
        :param str victim_name:
            Victim name in string
        :param str victim_name:
            Name of the punished
        :param str victim_steamid:
            SteamID of the punished
        :param str victim_ip:
            IP of the punished
        :param str admin_name:
            Name of admin, that applied punish
        :param str admin_steamid:
            SteamID admin, that applied punish
        :param str reason:
            Reason why player is punished
        :param int duration:
            Duration of the punishment
        """

        with db_cursor(self.db) as cur:
            # There's 4 tables. Which to chose?

            # If type is Kick, choose once
            if ptype == Punishment_types.KICK.value[0]:
                cur.execute(f"INSERT INTO 'once' "
                "(date, type, vname, vsteamid, vip, aname, asteamid, reason) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?)",
                (time(), ptype, victim_name, victim_steamid, victim_ip, admin_name,
                 admin_steamid, reason))

            # If duration is -1 (forever), choose permanent
            elif duration == -1:
                cur.execute(f"INSERT INTO 'permanent' "
                "(date, type, vname, vsteamid, vip, aname, asteamid, reason) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?)",
                (time(), ptype, victim_name, victim_steamid, victim_ip, admin_name,
                 admin_steamid, reason))

            # If duration > 0, send to to active table
            elif duration > 0:
                cur.execute(f"INSERT INTO 'active' "
                "(date, type, vname, vsteamid, vip, aname, asteamid, reason, duration) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (time(), ptype, victim_name, victim_steamid, victim_ip, admin_name,
                 admin_steamid, reason, duration))

            # Nothing came up? Log and raise an error!
            else:
                wcs_logger('error', f'Wrong arguments in DB_Admin.add_entry. Arguments: \n'
                    f'type = {ptype}\nvictim_name = {victim_name}\n'
                    f'victim_steamid = {victim_steamid}\nvictim_ip = {victim_ip}\n'
                    f'admin_name = {victim_name}\nadmin_steamid = {admin_steamid}\n'
                    f'reason = {reason}', console=True)
                raise ValueError

        # Saving changes
        self.db.commit()

    def _update_active(self):
        """
        Forces update active -> history,
        if not activated by self.Repeat
        """

        # Loading all data from active
        with db_cursor(self.db) as cur:
            cur.execute("SELECT rowid, * FROM 'active'")
            data = cur.fetchall()

        # List that collects all passed punishments
        expired = []

        # Checking all entry's
        for line in data:

            date_issued = line[1]
            duration = line[9]
            current_date = time()

            # If time passed
            if date_issued + duration < current_date:

                # Adding entry to passed
                expired.append(line)

                # Moving entry to history
                with db_cursor(self.db) as cur:

                    # Deleting line from 'active'
                    cur.execute(f"DELETE FROM 'active' WHERE rowid = {line[0]}")

                    # Adding time passed to line
                    line = list(line)
                    line.append(current_date)

                    # Adding line to 'history'
                    cur.execute(f"INSERT INTO 'history' "
                    "(date, type, vname, vsteamid, vip, aname, asteamid, reason, duration, expire_time) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", line[1:])

                # Firing event
                event = Punishment_expired()
                event.date_issued = line[1]
                event.date_expired = line[10]
                event.etype = line[2]
                event.victim_name = line[3]
                event.victim_steamid = line[4]
                event.victim_ip = line[5]
                event.admin_name = line[6]
                event.admin_steamid = line[7]
                event.reason = line[8]
                event.duration = line[9]
                event.fire()

        # Saving changes
        self.db.commit()

        # Returning list with overridden entry's
        return expired

    def check_for_active(self, steamid, ip, include_dates = False, include_reason = False) -> list:
        """
        Checking, if player has punishments with this SteamID and IP

        :param str steamid:
            SteamID of player
        :param str ip:
            IP of player
        :param bool include_dates:
            If True, adds date and duration of punishment to the return list
        :param bool include_reason:
            If True, returns reason in list
        """

        # Updating all active before checks
        self._update_active()

        all_punishments = []
        with db_cursor(self.db) as cur:
            # Getting permanent punishments
            cur.execute(f"SELECT type{', date' if include_dates else ''}"
                        f"{', reason' if include_reason else ''}"
                        f" FROM 'permanent' WHERE vsteamid = ? OR vip = ?",
                        (steamid, ip))

            # Adding to list
            all_punishments.extend(cur.fetchall())

            # Getting timed (active table) punishments
            cur.execute(f"SELECT type{', date, duration' if include_dates else ''}"
                        f"{', reason' if include_reason else ''}"
                        f" FROM 'active' WHERE vsteamid = ? OR vip = ?",
                        (steamid, ip))

            # Adding to list
            all_punishments.extend(cur.fetchall())

            # Returning list with all punishments
            return all_punishments

    def _unload_instance(self) -> None:
        """ Method that safely unloads database """

        # Stopping update repeat
        self.repeat.stop()

        # Checking last time for expired
        self._update_active()

        # Committing changes
        self.db.commit()

        # Closing connection to db
        self.db.close()

        # Logging close
        wcs_logger('db', f'DB_admin closing')

class _Disconnected_players:
    """
    Saves all disconnected players.
    • Can be iterable. Iterates over all players,
    and returns list [date of disconnect, name, steamid, ip]
    • Use .add_entry with name, steamid and ip as arguments
    to add someone to list
    • Use .get_info to get all players in one list
    """
    __slots__ = ('path_to_settings', 'json', 'position')

    def __init__(self, path: str):
        """

        :param str path:
            Determines where db is located. Absolute path
        """

        self.path_to_settings = path

        # Checking if file exist
        if not isfile(path):

            # No, doesn't. Creating file with one value
            with open(self.path_to_settings, 'w', encoding="utf-8") as file:
                dump([], file, ensure_ascii = False)

        # Reading JSON
        with open(path, encoding="utf-8") as file:
            try:
                self.json = loads(file.read())
            except JSONDecodeError:
                wcs_logger('EXCEPTION', 'JSONDecodeError in Disconnected_players')
                raise ValueError('JSONDecodeError in Disconnected_players')

    def __iter__(self):
        self.position = 0
        return self

    def __next__(self):
        try: x = self.json[self.position]
        except IndexError: raise StopIteration
        self.position += 1
        return x

    def add_entry(self, name, steamid, ip):
        """
        Adding new left player to list

        :param str name:
            name of left player
        :param str steamid:
            SteamID of left player
        :param ip
            IP of left player
        """

        # Checking if entry exist
        for index, player in enumerate(self.json):
            if player[2] == steamid:

                # Exist. Kicking it
                self.json.pop(index)

                # There's no repeats, so quit iteration
                break

        # Adding new entry to the list
        self.json.append([time(), name, steamid, ip])

        # Popping last element
        if len(self.json) > history_count:
            self.json.pop[0]

    def get_info(self):
        """Returning list with all left players"""
        return self.json

    def _unload_instance(self) -> None:
        """ CLosing class, saving information """

        # Saving information about players to JSON
        with open(self.path_to_settings, 'w', encoding="utf-8") as file:
            dump(self.json, file, ensure_ascii = False)

# Creating singletons
DB_admin         =   _DB_admin             (PATH_DATABASE_ADMIN)
DC_history       =   _Disconnected_players  (PATH_JSON_DISCONNECTED_PLAYERS)