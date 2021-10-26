# ../WCSSkills/db/wcs.py
# =============================================================================
# >> IMPORTS
# =============================================================================

# Python Imports
# Database
import sqlite3
# Json loader
from json import loads, dump
# Python paths
from os.path import isfile
# Typing
from typing import Union

# Plugin Imports
from .functions import db_cursor
# Paths
from WCSSkills.other_functions.constants import PATH_FILE_DATABASE_USERS
from WCSSkills.other_functions.constants import PATH_FILE_JSON_SKILLS_INFO
from WCSSkills.other_functions.constants import PATH_FILE_JSON_PLAYER_SETTINGS
# Logger
from WCSSkills.other_functions.functions import wcs_logger

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('DB_users',
           'Skills_info',
           'Player_settings')

# =============================================================================
# >> Classes
# =============================================================================

class _DB_users:
    """
    Class that realizes work with database:
    • Connecting users.db
    • Adding new players
    • Reading WCS-based player info
    """
    __slots__ = ('db',)

    def __init__(self, path_to_db):
    # On creating instance connect db

        # Connecting db
        self.db = sqlite3.connect(path_to_db)

        # Setting Pragmas
        with db_cursor(self.db) as cur:
            cur.execute('PRAGMA main.synchronous = NORMAL')
            cur.execute('PRAGMA main.journal_mode = OFF')
            cur.execute('PRAGMA temp_store = MEMORY')

    def info_load(self, steamid: str) -> dict:
    # Loading player data from db. Returns dict

        with db_cursor(self.db) as cur:

            # Check if table exists
            cur.execute(f"SELECT name FROM sqlite_master WHERE type = 'table' AND name = '{steamid}.info'")

            if len(cur.fetchall())==0:
                self._new_player(steamid=steamid)

            # Extracting data
            cur.execute(f"SELECT * FROM '{steamid}.info'")
            data = dict()
            for value in cur.fetchall():
                data[value[0]] = value[1]
        return data

    def info_save(self, steamid: str, data: list) -> None:
    # Saving player data to db

        with db_cursor(self.db) as cur:
            # Updating values
            cur.executemany(f"INSERT OR REPLACE INTO '{steamid}.info' (name, value) VALUES (?, ?)", data)
        self.db.commit()

    def skills_load(self, steamid: str) -> dict:

        with db_cursor(self.db) as cur:

            # Loading data about skills from table
            cur.execute(f"SELECT * FROM '{steamid}.skills'")
            data_list = cur.fetchall()

        # Transforming to readable variant
        data_dict = dict()
        for num, value in enumerate(data_list):
            value = list(value)
            value[4] = eval(f"{value[4]}")
            data_dict[value[0]] = value[1:]

        return data_dict

    def skills_save(self, steamid: str, data_skills: dict) -> None:

        temp = []
        for key, value in data_skills.items():
            new_line = [key]
            new_line.extend(value)
            temp.append(new_line)
        data_skills = temp
        del temp

        # Transforming types to string
        for num, value in enumerate(data_skills):
            value = list(value)
            value[4] = f"{value[4]}"
            data_skills[num] = value

        # Saving
        with db_cursor(self.db) as cur:
            cur.executemany(f"INSERT OR REPLACE INTO '{steamid}.skills' "
            "(name,lvl,xp,lvl_selected,settings) VALUES (?,?,?,?,?)", data_skills)
        self.db.commit()

    def _new_player(self, steamid: str) -> None:
    # Function to create new tables in db, if player doesn't exist

        wcs_logger('db', f'New player tables with steamID {steamid} created')

        with db_cursor(self.db) as cur:

            # Creating steamid.info table
            cur.execute(f"""CREATE TABLE "{steamid}.info"(  
                name TEXT NOT NULL UNIQUE,
                value INT
                )"""
            )
            data = [("total_lvls", 0),
                    ("skills_selected", "['Empty','BLOCKED','BLOCKED','BLOCKED','BLOCKED']"),
                    ("LK_lvls", 100)]
            for setting in Player_settings.get_values():
                data.append((setting,Player_settings.get_default_value(setting)))

            cur.executemany(f"INSERT INTO '{steamid}.info' (name, value) VALUES (?,?)", data)

            # Creating steamid.races table
            cur.execute(f"""CREATE TABLE "{steamid}.skills"(
                name TEXT NOT NULL UNIQUE,
                lvl INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                lvl_selected INTEGER,
                settings TEXT
                )"""
        )

        self.db.commit()

    def unload_instance(self) -> None:
        wcs_logger('db', f'DB_users closing')
        self.db.commit()
        self.db.close()

class _DB_skills:
    """
    Class that realizes loading info about skills:
    • Name
    • Description
    • Maximum level to upgrade
    • Min player lvl to achieve
    """
    __slots__ = ('json',)

    def __init__(self, path_to_skills) -> None:
        if not isfile(path_to_skills):
            with open(path_to_skills, 'w', encoding="utf-8") as f:
                dump({
                    "Health": {
                        "name": "Здоровье",
                        "description": ["Крепкое тело!",
                            "Вы станете более выносливым."],
                        "max_lvl": 1000,
                        "min_player_lvl": 0,
                        "settings_type": {},
                        "settings_name": {},
                        "settings_cost": {}
                    }
                }, f, ensure_ascii=False)

        with open(path_to_skills, encoding="utf-8") as file:
            self.json = loads(file.read())

    def get_skill(self, skill_name: str) -> dict:
        return self.json[skill_name]

    def get_names(self) -> tuple:
        return tuple([value["name"] for value in self.json.values()])

    def get_name(self, skill_name: str) -> str:
        return self.json[skill_name]['name']

    def get_classes(self) -> tuple:
        return tuple([skill for skill in self.json])

    def get_min_lvl(self, skill_name: str) -> int:
        return self.json[skill_name]['min_player_lvl']

    def get_max_lvl(self, skill_name: str) -> int:
        return self.json[skill_name]['max_lvl']

    def get_description(self, skill_name: str) -> list:
        return self.json[skill_name]['description']

    def get_settings_type(self, skill_name: str, setting: str = None) -> Union[list, str]:
        if setting is None:
            return self.json[skill_name]['settings_type']
        else:
            return self.json[skill_name]['settings_type'][setting]

    def get_settings_name(self, skill_name: str, setting: str = None) -> Union[list, str]:
        if setting is None:
            return self.json[skill_name]['settings_name']
        else:
            return self.json[skill_name]['settings_name'][setting]

    def get_settings_cost(self, skill_name: str, setting: str = None) -> Union[list, str]:
        if setting is None:
            return self.json[skill_name]['settings_cost']
        else:
            return self.json[skill_name]['settings_cost'][setting]


class _Player_settings:
    """
    Class that realizes loading info about player settings:
    • Name
    • Default value
    """
    __slots__ = ('json',)

    def __init__(self, path_to_settings: str):

        # Checking if file exist
        if not isfile(path_to_settings):

            # No, doesn't. Creating file with one value
            with open(path_to_settings, 'w', encoding="utf-8") as file:
                dump({
                    "skills_activate_notify": {
                        "name": "Умения в начале раунда в чате",
                        "default_value": True }
                    }, file, ensure_ascii=False)

        # Reading JSON
        with open(path_to_settings, encoding="utf-8") as file:
            self.json = loads(file.read())

    def get_default_value(self, setting: str) -> str:
        """Returns default value of selected setting"""

        return self.json[setting]['default_value']

    def get_name(self, setting: str = None) -> Union[list, str]:
        """
        Get name of setting, if needed
        Else get list of all names
        """

        if setting is None:
            names = []
            for setting in self.json.values():
                names.append(setting['name'])
            return names
        else:
            return self.json[setting]['name']

    def get_values(self) -> list:
        return self.json.keys()

# Creating singletons
DB_users         =   _DB_users         (PATH_FILE_DATABASE_USERS)
Skills_info      =   _DB_skills        (PATH_FILE_JSON_SKILLS_INFO)
Player_settings  =   _Player_settings  (PATH_FILE_JSON_PLAYER_SETTINGS)