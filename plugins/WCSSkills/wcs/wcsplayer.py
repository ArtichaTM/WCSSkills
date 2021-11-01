# ../WCSSkills/wcs/wcsplayer.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# Random
from random import uniform as randfloat

# Source.Python Imports
# Players
from players.entity import Player
from players.helpers import index_from_userid
# Events
from events import Event
from events import event_manager
# Listeners
from listeners.tick import Delay
# Server status
from engines.server import server
# PlayerIter
from filters.players import PlayerIter
# SayText2
from messages.base import SayText2

WCS_Players = dict()
# Plugin Imports
# Databases
from WCSSkills.db.wcs import DB_users, Skills_info, Player_settings
from WCSSkills.db.admin import DC_history
# Ultimate, ability, etc
from WCSSkills.commands.buttons import Buttons
# Skills
from WCSSkills.skills.skills import *
# Typing types
from WCSSkills.python.types import *
# Constants
from WCSSkills.other_functions.constants import WCS_FOLDER
from WCSSkills.other_functions.constants import SKILL_SETTING_DEFAULT_BOOL
# Logger
from WCSSkills.other_functions.functions import wcs_logger
# Xp calculator
from WCSSkills.other_functions.xp import next_lvl_xp_calculate as next_xp
# Delay for skill deactivation
from WCSSkills.other_functions.functions import skill_timings_calculate

# =============================================================================
# >> Events on loading/unloading player
# =============================================================================

@Event('player_activate')
def WCS_Player_load(ev) -> None:
    """ When player connects (usually), initialize WCS_Player and load his data """

    # Check if new player is a bot
    if Player(index_from_userid(ev['userid'])).steamid == 'BOT':
        # Then canceling function
        return

    # Loading WCS_Players
    global WCS_Players

    # Creating user variable, so we can extract userid
    user: wcs_player_entity = WCS_Player(ev['userid'])

    # Adding WCS_Player in the dict
    WCS_Players[user.userid]: wcs_player_entity = user


@Event('player_disconnect')
def WCS_Player_unload(ev) -> None:
    """ When player disconnects, save data to db and delete him from WCS_Players """

    # Check if event called on BOT
    if ev['networkid'] == 'BOT':
        # Then canceling function
        return

    # Loading WCS_Players
    global WCS_Players

    # Is this player is WCS_Player?
    try:
        # Yes, getting WCS_Players
        user: wcs_player_entity = WCS_Players[ev['userid']]

    except KeyError:

        # No. Logging warning and returning
        wcs_logger('player state', 'User without '
                                   'WCS_Player disconnected', console=True)
        return
    else:
        # If nothing bad happened,

        # Unloading player
        user.unload_instance()

        # And popping him from the dict
        WCS_Players.pop(ev['userid'])


# =============================================================================
# >> WCS_Player class
# =============================================================================

class WCS_Player(Player): # Short: WCSP
    """

    Class that realizes player-based WCS functionality:
    • Race select
    • Saving player skills
    • Working with

    Works with classes, that realizes:
    • database functionality (DB_users)
    • race functionality (skills.py)
    • player settings (Skills_info)

    """

    def __init__(self, userid: int, caching: bool = True):

        # Executing Player __init__
        super().__init__(index_from_userid(userid), caching)

        # Setting target_name
        self.target_name = f"WCSP_{self.index}"

        # Loading information about player from databases
        self.data_info = DB_users.info_load(self.steamid)
        self.data_skills = DB_users.skills_load(self.steamid)

        # Basic information
        # Lvl of account (Summary of all skills)
        self.total_lvls = self.data_info["total_lvls"]
        # Skills that player lastly selected
        self.skills_selected = eval(self.data_info["skills_selected"])
        # Levels in lvl bank
        self.lk_lvls = self.data_info["LK_lvls"]
        # Variable to change skills
        self.skills_change = [None, None, None, None, None]

        # Selected skills information
        # Max achieved lvl
        self.skills_selected_lvls = [None, None, None, None, None]
        # Selected (if sel.) level
        self.skills_selected_lvl = [None, None, None, None, None]
        # Xp of skill
        self.skills_selected_xp = [None, None, None, None, None]
        # Max xp, after which player lvls up
        self.skills_selected_next_lvl = []
        # Settings of skill
        self.skills_selected_settings = [None, None, None, None, None]

        # Loading information from data_skills into skills info
        for num, skill in enumerate(self.skills_selected):
            if skill is None or skill == 'Empty' or skill == 'BLOCKED':

                # If no skill selected, there's no need to change anything
                continue

            else:

                # Skills exist, searching for skill data in data_skills
                data = self.data_skills[skill]

                # Applying data to lists
                self.skills_selected_lvls[num] = data[0]
                self.skills_selected_xp[num] = data[1]
                self.skills_selected_lvl[num] = data[2]
                self.skills_selected_settings[num] = data[3]

        # Adding max xp (after which player lvl up)
        for value in self.skills_selected_lvls:

            # Checking, if there's any skill in the slot
            if value is None:

                # No, then place 'None' in the max xp list
                self.skills_selected_next_lvl.append(None)
                continue

            else:

                    # Skill exist, calculating new_lvl value
                    self.skills_selected_next_lvl.append(
                        next_xp(value))

        # Skills, that is active right now
        # • Added at start of round
        # • Cleared in the end of round (pre_restart)
        self.skills_active = set()

        # Holds information for functions, that uses keyboard enter
        self.enter_temp = None

        # XP multiplier (not used right now). Multiply happens after all functions
        self.xp_multiplier = 1

        # lvls, that player has in Level Bank (LK)
        self.lk_lvls = 100000

        # Loading player settings
        for setting in Player_settings.get_values():
            self.data_info[setting] = Player_settings.get_default_value(setting)

        # Ultimate and Ability class
        self.Buttons = Buttons(self)

        # Registering WCS_Player for skills activate/deactivate
        event_manager.register_for_event('round_start', self.skills_activate)
        event_manager.register_for_event('player_death', self.skills_deactivate)
        event_manager.register_for_event('round_end', self.skills_deactivate)

        # Logging initialization
        wcs_logger("player state", f"{self.name}: WCS_Player initialized")

    def skills_activate(self, _=None) -> None:
        """
        Activate skills. Usually in the start of round
        • Adding new skills to data_skills, if player never had this skill before
        • Saving data_skills at the end of initialization
        • Changing active skills (applying skills_change into self.skills_selected)
        • Loading Buttons (for ult and abi)
        • Rejects skill repeats (first - loading, second - reject)
        """

        # Is skills turned off?
        if len(self.skills_active) != 0:

            # They're active! Turn them off, then run active
            self.skills_deactivate()

        # Check if new skills exist
        owned_skills = set([skill_name for skill_name in self.data_skills])
        change_skills = set(self.skills_change).difference({None, 'Empty'
                              }) if set(self.skills_change) != {None} else None

        if change_skills is not None:
            for skill in change_skills.difference(owned_skills):
                # Logging
                wcs_logger('skill change', f"{self.name}: Selected new skill {skill}")

                # Adding new entry
                self.data_skills[skill] = (0, 0, None, {})

        # First loop created to check, if there's skill that should be changed
        for num, skill_change in enumerate(self.skills_change):

            # If this skill really exist:
            if skill_change is not None:

                # Saving previous skill
                previous_skill: str = self.skills_selected[num]
                if previous_skill is not None and previous_skill != 'Empty' and \
                        previous_skill != 'BLOCKED':
                    self.data_skills[previous_skill] = (self.skills_selected_lvls[num],
                                                        int(self.skills_selected_xp[num]),
                                                        self.skills_selected_lvl[num],
                                                        self.skills_selected_settings[num])

                # Loading info about new skill
                skill_name = skill_change

                if 'skill_name' not in locals() or skill_name == 'Empty':
                    self.skills_selected[num]: str = 'Empty'
                    self.skills_selected_lvls[num]: int = None
                    self.skills_selected_xp[num]: int = None
                    self.skills_selected_next_lvl[num]: int = None
                else:
                    skill_lvl, skill_xp, skill_lvl_selected, \
                    skill_settings = self.data_skills[skill_change]

                    self.skills_selected[num]: str = skill_name
                    self.skills_selected_lvls[num]: int = skill_lvl
                    self.skills_selected_xp[num]: int = skill_xp
                    self.skills_selected_settings[num]: int = skill_settings
                    self.skills_selected_next_lvl[num]: int = next_xp(skill_lvl)
                    print(self.skills_selected_next_lvl[num])

                # Logging skill change
                wcs_logger('skill change', f"{self.name}: {previous_skill} -> {skill_name}")

            self.skills_change[num] = None

        # Anti-repeat variable
        loaded = set()

        # Activating skills
        for num, skill in enumerate(self.skills_selected):

            # Checking, if slot empty or blocked and reject repeating
            if skill != 'Empty' and skill != 'BLOCKED' and skill not in loaded:

                # Dictionary for skill settings
                skill_settings: dict = Skills_info.get_settings_type(skill)

                # If settings in WCSP doesn't equal Skills_info,
                # Checking every setting in skills_selected_settings
                if len(self.skills_selected_settings[num]) != len(skill_settings):

                    # Iterating over each skill setting in DB
                    for setting in skill_settings:

                        # If this setting doesn't exist, add it
                        if setting not in self.skills_selected_settings[num]:

                            # Check for skill type
                            if skill_settings[setting] == 'bool':
                                # If bool, setting to default value (False)
                                self.skills_selected_settings[num][setting] = SKILL_SETTING_DEFAULT_BOOL

                # Checking for custom lvl selected
                if self.skills_selected_lvl[num] is None:

                    # Not selected, calling with maximum lvl
                    self.skills_active.add(eval(f"{skill}({self.userid},"
                                                f"{self.skills_selected_lvls[num]},"
                                                f"{self.skills_selected_settings[num]})"))
                else:

                    # Selected custom lvl, calling with selected lvl
                    self.skills_active.add(eval(f"{skill}({self.userid},"
                                                f"{self.skills_selected_lvl[num]},"
                                                f"{self.skills_selected_settings[num]})"))

                # Adding to not-repeat list
                loaded.add(skill)

        # Ultimate/Ability binds
        self.Buttons.round_start()

        # Notifying player, if he has no active skills
        if len(self.skills_active) == 0:
            SayText2(f"\4[WCS]\1 У вас нет активных навыков").send(self.index)

        # Updating data_skills
        Delay(randfloat(1, 4), self._data_skills_update)

        # Logging
        wcs_logger('skills', f"{self.name}: started round with "
                             f"{', '.join(self.skills_selected)}.")

    def _skills_deactivate(self):
        """ Deactivates skills in the end of round"""

        # Iterating over all skills
        for skill in self.skills_active:

            # Deactivating them
            skill.close()

        # Clearing skills_active, bcz no skills active :D
        self.skills_active.clear()

        # Unloading ultimate/ability
        self.Buttons.unload()

    def skills_deactivate(self, ev=None) -> None:

        # Calculating values for round_end
        delay = skill_timings_calculate()

        # Checking for custom deactivate
        if ev is None:
            self._skills_deactivate()
            return

        # Is skills turned on?
        if len(self.skills_active) == 0:

            # Skills deactivated! Abort skills deactivation
            return

        # Check what event is fired
        if ev.name == 'player_death':

            # If player_death, died player might be NOT the owner
            if ev['userid'] == self.userid:

                # It's the owner. Deactivate
                self._skills_deactivate()

        elif ev.name == 'round_end':

            # Round end event, deactivate with delay, to make
            # skills active even after round end
            Delay(delay, self._skills_deactivate)

    def _data_skills_update(self):
        for num, skill in enumerate(self.skills_selected):
            if skill != 'Empty' and skill != 'BLOCKED':
                self.data_skills[skill] = (self.skills_selected_lvls[num],
                                           int(self.skills_selected_xp[num]),
                                           self.skills_selected_lvl[num],
                                           self.skills_selected_settings[num])

    def _data_info_update(self):
        self.data_info["total_lvls"]: int = self.total_lvls
        self.data_info['skills_selected']: str = f"{self.skills_selected}"
        self.data_info["LK_lvls"]: int = self.lk_lvls

    def heal(self, hp, ignore=False) -> int:

        # If ignoring max_hp, add all hp
        if ignore:
            self.health += hp
            return hp

        # Detecting if hp is below max_hp
        insufficiency: int = self.max_health - self.health

        # If player on max_hp or above, no hp will be added and return 0
        if insufficiency <= 0:
            return 0

        # If player can be healed, but hp will overheal (after heal health>max_health)
        elif hp >= insufficiency:
            self.health += insufficiency
            return insufficiency

        # If nothing happened, healed hp will not be at max_health
        else:
            self.health += hp
            return hp

    def add_xp(self, amount: int, reason: str = None) -> None:
        pass
        skills_amount: int = len(self.skills_active)
        if skills_amount == 0:
            return
        if self.data_info['xp_add_notify']:
            # Notifying player about added xp
            if reason is None:
                # If reason is not present
                SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 опыта").send(self.index)
            else:
                # If reason is present
                SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 "
                         f"опыта за \5{reason}\1").send(self.index)
        amount: float = amount // skills_amount

        # Going through every skill
        for num, current_xp in enumerate(self.skills_selected_xp):

            if self.skills_selected[num] is None or \
                    self.skills_selected[num] == 'Empty' or \
                    self.skills_selected[num] == 'BLOCKED':
                continue

            # Checking, if in this slot skill is present
            if current_xp is None:
                continue

            # Adding xp
            self.skills_selected_xp[num] += amount

            leveled_up = False

            # Adding lvl, if there's enough xp
            while self.skills_selected_xp[num] > self.skills_selected_next_lvl[num]:

                # Leveled up?
                leveled_up = True

                # Adding lvl
                self.skills_selected_lvls[num] += 1

                # Adding +1 to overall lvls count
                self.total_lvls += 1

                # Subtracting xp, that needed to lvl up
                self.skills_selected_xp[num] -= self.skills_selected_next_lvl[num]

                # Adding new max_xp
                self.skills_selected_next_lvl[num] = next_xp(
                                            self.skills_selected_lvls[num])

                # Notifying player
                SayText2("\4[WCS]\1 Вы повысили уровень навыка "
                         f"\4{Skills_info.get_name(self.skills_selected[num])}\1 "
                         f"до \5{self.skills_selected_lvls[num]}\1").send(self.index)

            if leveled_up and self.data_info['sound_level_up']:

                # Playing sound
                self.emit_sound(f'{WCS_FOLDER}/level_up.mp3',
                                attenuation=1.1,
                                volume = 0.5
                                )

    def unload_instance(self) -> None:
        """ Func saves player data to db's and remove WCS_Player from WCS_Players """

        # Event unregister
        event_manager.unregister_for_event('round_start', self.skills_activate)
        event_manager.unregister_for_event('round_end', self.skills_deactivate)
        event_manager.unregister_for_event('player_death', self.skills_deactivate)

        # Deactivating skills
        self.skills_deactivate()

        # Saving skills data to self.data_skills
        self._data_skills_update()

        # Saving settings and other info to self.data_info
        self._data_info_update()

        # Saving info to db's
        DB_users.info_save(self.steamid, [("total_lvls", self.total_lvls),
                                          ("skills_selected", f"{self.skills_selected}"),
                                          ("LK_lvls", self.lk_lvls)])
        DB_users.skills_save(self.steamid, self.data_skills)
        DC_history.add_entry(self.name, self.steamid, self.address)

        # Logging
        wcs_logger('player state', f"{self.name} WCS_Player unloaded")


# =============================================================================
# >> Other
# =============================================================================

# Checking if server is running on plugin load
if server.is_active():

    # If running, adding every player to WCS_Players set
    for player in PlayerIter():
        # Calling load function
        WCS_Player_load({'userid': player.userid})

# =============================================================================
# >> Imports that use WCS_Player
# =============================================================================
