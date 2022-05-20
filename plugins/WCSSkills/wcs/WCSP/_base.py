# ../WCSSkills/wcs/_base.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# Typing
from typing import Union, Iterable, Dict, List
# Random
import random

# Source.Python Imports
# Players
import WCSSkills.WCS_Logger
from players.entity import Player
from players.helpers import index_from_userid, userid_from_index
# Events
from events import Event
from events import event_manager
# Listeners
from listeners.tick import Delay
# Server status
from engines.server import server
# Iterators
from filters.players import PlayerIter
# SayText2
from messages.base import SayText2
# Entity
from entities.entity import Entity

WCS_Players = dict()
# Plugin Imports
# Databases
import WCSSkills.db as db
# Ultimate, ability, etc
from WCSSkills.commands.buttons import Buttons
# Skills
from WCSSkills import skills
# Typing types
from WCSSkills.python.types import *
# DefaultDict
from WCSSkills.python.dictionaries import DefaultDict
# Other_functions module
import WCSSkills.other_functions as other_functions
# XP


# =============================================================================
# >> Functions
# =============================================================================
required_xp = lambda lvl: ((80 * lvl+1 ** 0.5) ** 2) ** 0.5
next_lvl_xp_calculate = lambda lvl: required_xp(lvl) - random.randint(0, int(required_xp(lvl) // 2))

# =============================================================================
# >> Events on loading/unloading player
# =============================================================================
@Event('player_activate')
def player_load(ev) -> None:
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
def player_unload(ev) -> None:
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
        WCSSkills.WCS_Logger.wcs_logger('player state', 'User without '
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
    • database functionality (wcs.DB_users)
    • race functionality (skills.py)
    • player settings (wcs.Skills_info)

    """

    def __init__(self, userid: int, caching: bool = True):
        super().__init__(index_from_userid(userid), caching)

        # Setting target_name
        self.target_name = f"WCSP_{self.index}"

        # Loading information about player from databases

        # Dict[skill_name] = List[lvl, xp, selected_lvl, settings_dict]
        self.data_skills: Dict[str, List[int, int, Union[None, int], Dict]
            ] = db.wcs.DB_users.skills_load(self.steamid)

        # Settings, levels, etc...
        self.data_info: dict = db.wcs.DB_users.info_load(self.steamid)

        # Basic information
        # Lvl of account (Summary of all skills)
        self.total_lvls: int = self.data_info["total_lvls"]
        # Levels in lvl bank
        self.lk_lvls: int = self.data_info["LK_lvls"]
        # Variable to change skills
        self.skills_change = [None, None, None, None, None]

        # Affinity. 'Light'/'Dark'/'' for now
        self.affinity = other_functions.constants.AffinityTypes.NONE

        # Selected skills information
        # Skills that player lastly selected
        self.skills_selected: list = eval(self.data_info["skills_selected"])
        # Max achieved lvl
        self.skills_selected_lvls = [None, None, None, None, None]
        # Selected (if selected, otherwise None) level
        self.skills_selected_lvl = [None, None, None, None, None]
        # Xp of skill
        self.skills_selected_xp = [None, None, None, None, None]
        # Max xp, after which player levels-up up
        self.skills_selected_next_lvl = [None, None, None, None, None]
        # Settings of skill
        self.skills_selected_settings = [None, None, None, None, None]

        # Loading information from data_skills into skills info
        for num, skill in enumerate(self.skills_selected):
            if skill is None or skill == 'Empty' or skill == 'BLOCKED':
                # No skill selected, or slot blocked

                # Nothing changed
                continue

            else:
                # Skill exist

                # Searching for skill data in data_skills
                data = self.data_skills[skill]

                # May be skill has been changed, and now user level below required?

                # Getting skill minimum level
                min_lvl = db.wcs.Skills_info.get_min_lvl(self.skills_selected[num])

                # Enough lvl?
                if min_lvl > self.total_lvls:
                    # No, minimum above player total

                    # Excluding skill
                    self.skills_selected[num] = None

                    # Continue iteration
                    continue

                # Applying data to lists
                self.skills_selected_lvls[num] = data[0]
                self.skills_selected_xp[num] = data[1]
                self.skills_selected_lvl[num] = data[2]
                self.skills_selected_settings[num] = data[3]

        # Adding max xp (after which player lvl up)
        for index, value in enumerate(self.skills_selected_lvls):

            # Checking, if there's any skill in the slot
            if value is None:

                # No, then place 'None' in the max xp list
                self.skills_selected_next_lvl[index] = None

            else:

                # Skill exist, calculating new_lvl value
                self.skills_selected_next_lvl[index] = \
                    next_lvl_xp_calculate(value)

        # Skills, that is active right now
        # • Added at start of round
        # • Cleared in the end of round (pre_restart)
        self._skills_active = set()

        # Holds information for functions, that uses keyboard enter
        self.enter_temp = None

        # XP multiplier (not used right now (doesn't change I mean)).
        # Multiply happens after all functions
        self.xp_multiplier: float = 1

        # Healing multiply
        self.heal_multiplier: float = 1

        # Level Bank (LK) levels amount
        self.lk_lvls: float = 100000

        # Immune to various skills of WCS_Player
        self.immunes = DefaultDict()
        self.immunes.add_ignored(0)
        self.immunes.set_default(other_functions.constants.ImmuneTypes.Nothing)

        # Loading player settings
        for setting in db.wcs.Player_settings.get_values():
            self.data_info[setting] = db.wcs.Player_settings.get_default_value(setting)

        # Ultimate and Ability class
        self.Buttons = Buttons(self)

        # Registering WCS_Player for skills activate/deactivate
        event_manager.register_for_event('round_start', self.skills_activate)
        event_manager.register_for_event('player_death', self.skills_deactivate)
        event_manager.register_for_event('round_end', self.skills_deactivate)

        # Logging initialization
        WCSSkills.WCS_Logger.wcs_logger("player state", f"{self.name}: WCS_Player initialized")

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(name={self.name},"
               f"index={self.index}, userid={self.userid})")

    def __eq__(self, other) -> bool:
        if self.__class__ is other.__class__: return self.index == other.index
        else: raise NotImplemented

    @staticmethod
    def iter():
        """ Iterating over active WCS_Players
        :return: Iterable
        """
        for WCSP in WCS_Players.values(): yield WCSP

    @staticmethod
    def from_userid(userid, **_):
        """ Getting WCS_Player by userid
        :param userid: userid of desired player
        :return: None, if no WCS_Player found. Otherwise, WCS_Player instance
        """
        try: return WCS_Players[userid]
        except KeyError: return None

    @staticmethod
    def from_index(index):
        """ Getting WCS_Player by userid
        :param index: index of desired player
        :return: None, if no WCS_Player found. Otherwise, WCS_Player instance
        """
        try: return WCS_Players[userid_from_index(index)]
        except KeyError: return None

    @property
    def invisibility(self) -> None:
        ...

    @invisibility.setter
    def invisibility(self, amount: int) -> None:
        """ Setting player invisibility by values [0,255]
        :param amount: invisibility amount
        :return: None
        """
        assert isinstance(amount, int), "invisibility takes only integers"
        assert (0 <= amount <= 255), "invisibility should be in range from 0 to 255"

        # Getting current player color
        color = self.color

        # Setting alpha
        color.a = amount

        # Applying new color to player
        self.color = color

    @invisibility.getter
    def invisibility(self) -> int:
        """ Getting current player invisibility
        :return: invisibility amount
        """
        return self.color.a

    def view_entity_offset(self, max_offset: int,
                           player_only: bool = True,
                           immune_type: str = 'presence',
                           check_type: other_functions.constants.ImmuneTypes =
                               other_functions.constants.ImmuneTypes.Default
                           ) -> Union[Entity, None]:
        """ Returns the most close entity to the crosshair
        :param max_offset: More value, more allowed angle. -1 <= offset <= 1
        :param player_only: Select entity with classname 'player'
        :param immune_type: Player only. Type of immune. By default, using ImmuneTypes.Default
        :param check_type: Player only. what type of immune we should check
        :return: Entity that player looking at, or None, if nothing at crosshair
        """

        # Input argument check
        assert (-1 <= max_offset <= 1), 'Wrong offset. Offset should be -1 <= offset <= 1'

        # Looking for entities or only players?
        if player_only:

            # Calling function for players
            entities = other_functions.functions.open_players(entity=self,
                form = check_type,
                type_of_check = immune_type,
                same_team=False)
        else:
            # Calling function for entities
            entities = other_functions.functions.open_entities(owner=self)

        # Nothing found? Return None
        if not entities: return None

        # Creating new list for offsets
        offsets = []

        for entity in entities:

            # Getting entity origin
            destination = entity.origin

            # Calculating view vector (view_vector to entity)
            awaited_ray = (destination - self.eye_location).normalized()

            # Calculating difference current_view_vector - needed_view_vector
            distance = self.view_vector.get_distance(awaited_ray)/2

            if max_offset < 0: distance = 1-distance

            # Setting offset
            offsets.append(distance)

        # Getting most close entity to crosshair
        minimum = min(offsets)

        # Above limit? Return None
        if minimum > abs(max_offset): return None

        # Otherwise, return closes entity
        return entities[offsets.index(minimum)]

    def players_around(self,
                       radius: float,
                       same_team: bool = False,
                       form: other_functions.constants.ImmuneTypes = None,
                       immune_type: str = None,
                       deflect_function: callable = lambda : None
                       ):
        """Returns WCS_Player's that within owner in some radius
        :param radius: radius to check in units
        :param same_team: Check for only same team with owner?
        :param form: ImmuneTypes form of attack
        :param immune_type: Which immune to check (paralyze/toss/...)
        :param deflect_function: Function, that will be called on immune deflect
        :return: WCS_Player
        """

        # Iterating over all alive WCS_Players
        for WCSP in self.iter():

            if same_team and WCSP.team_index != self.team_index: return

            # Continue to next player if shielded and shielding from that is ON
            if form is not None and skills.functions.immunes_check(
                    victim = WCSP,
                    form = form,
                    immune_type = immune_type,
                    deflect_target = deflect_function,
                    ) != other_functions.constants.ImmuneReactionTypes.Passed:
                return

            # Player inside radius?
            if self.origin.get_distance(WCSP.origin) <= radius:

                # Return this player
                yield WCSP

    def skills_activate(self, *_) -> None:
        """ Activates skills. Usually in the start of round
        • Adding new skills to data_skills, if player never had this skill before
        • Saving data_skills at the end of initialization
        • Changing active skills (applying skills_change into self.skills_selected)
        • Loading Buttons (for ult and abi)
        • Rejects skill repeats (first - loading, second - reject)
        """

        # Is skills turned off?
        if len(self._skills_active):
            # They're active!

            # Turn them off, then run activate
            self.skills_deactivate()

        # Reset heal multiplier
        self.heal_multiplier = 1

        # Check if new skills exist
        owned_skills = set([skill_name for skill_name in self.data_skills])
        change_skills = set(self.skills_change).difference({None, 'Empty'
                              }) if set(self.skills_change) != {None} else None

        if change_skills is not None:
            # There's new skills to change

            for skill in change_skills.difference(owned_skills):
                # Logging
                WCSSkills.WCS_Logger.wcs_logger('skill acquire',
                                        f"{self.name}: Selected new skill {skill}")

                # Adding new entry
                self.data_skills[skill] = (0, 0, None, {})

        # First loop created to check, if there's skill that should be changed
        for num, skill_change in enumerate(self.skills_change):

            # If this skill really exist:
            if skill_change is not None:

                # Saving previous skill
                previous_skill: str = self.skills_selected[num]

                # Is this is a skill?
                if previous_skill not in {None, 'Empty', 'BLOCKED'}:

                    # Saving information about previous skill
                    self.data_skills[previous_skill] = (self.skills_selected_lvls[num],
                                                        int(self.skills_selected_xp[num]),
                                                        self.skills_selected_lvl[num],
                                                        self.skills_selected_settings[num])

                # Loading info about new skill
                skill_name = skill_change

                if 'skill_name' not in locals() or skill_name == 'Empty':
                    # Skill slot is empty

                    self.skills_selected[num]: str = 'Empty'
                    self.skills_selected_lvls[num]: int = None
                    self.skills_selected_xp[num]: int = None
                    self.skills_selected_next_lvl[num]: int = None
                else:
                    # Skill is real
                    skill_lvl, skill_xp, skill_lvl_selected, \
                    skill_settings = self.data_skills[skill_change]

                    self.skills_selected[num]: str = skill_name
                    self.skills_selected_lvls[num]: int = skill_lvl
                    self.skills_selected_xp[num]: int = skill_xp
                    self.skills_selected_settings[num]: int = skill_settings
                    self.skills_selected_next_lvl[num]: int = \
                        next_lvl_xp_calculate(skill_lvl)

                # Logging skill change
                WCSSkills.WCS_Logger.wcs_logger('skill change',
                                        f"{self.name}: {previous_skill} -> {skill_name}")

            self.skills_change[num] = None

        # Anti-repeat variable
        loaded = set()

        # Activating skills
        for num, skill in enumerate(self.skills_selected):

            # Checking, if slot empty or blocked and reject repeating
            if skill != 'Empty' and skill != 'BLOCKED' and skill not in loaded:

                # Dictionary for skill settings
                skill_settings: dict = db.wcs.Skills_info.get_settings_type(skill)

                # If settings in WCSP doesn't equal wcs.Skills_info,
                # Checking every setting in skills_selected_settings
                if len(self.skills_selected_settings[num]) != len(skill_settings):

                    # Iterating over each skill setting in DB
                    for setting in skill_settings:

                        # If this setting doesn't exist, add it
                        if setting not in self.skills_selected_settings[num]:

                            # Check for skill type
                            if skill_settings[setting] == 'bool':
                                # If bool, setting to default value (False)
                                self.skills_selected_settings[num][setting] = \
                                    other_functions.constants.SKILL_SETTING_DEFAULT_BOOL

                # Getting needed skill

                # First we're accessing file, that stores this skill (immune/skill/...)
                skill_class = getattr(skills, skill[:skill.find('.')])

                # Then we're trying to find this skill in this file
                skill_class = getattr(skill_class, skill[skill.find('.')+1:])

                # Checking for custom lvl selected
                if self.skills_selected_lvl[num] is None:
                    # Maximum level
                    self._skills_active.add(skill_class(self.userid,
                                self.skills_selected_lvls[num],
                                self.skills_selected_settings[num]))

                else:
                    # Custom level
                    self._skills_active.add(skill_class(self.userid,
                                self.skills_selected_lvl[num],
                                self.skills_selected_settings[num]))

                # Adding to not-repeat list
                loaded.add(skill)

        # Ultimate/Ability binds activates with skill activate
        self.Buttons.round_start()

        # Notifying player, if he has no active skills
        if len(self._skills_active) == 0:
            SayText2(f"\4[WCS]\1 У вас нет активных навыков").send(self.index)

        # Updating data_skills
        Delay(random.uniform(1, 4), self._data_skills_update)

        # Logging
        WCSSkills.WCS_Logger.wcs_logger('skills', f"{self.name}: started round with "
                             f"{', '.join(self.skills_selected)}.")

    def _skills_deactivate(self):
        """ Deactivates skills in the end of round"""

        # Iterating over all skills
        for skill in self._skills_active:

            # Deactivating them
            skill.close()

        # Clearing skills_active, bcz no skills active :D
        self._skills_active.clear()

        # Unloading ultimate/ability
        self.Buttons.unload()

        # Clearing immunes
        self.immunes.clear()

        # Setting heal multiply to one
        self.heal_multiplier = 1

    def skills_deactivate(self, ev=None) -> None:

        # Checking for custom deactivate
        if ev is None:
            self._skills_deactivate()
            return

        # Is skills turned on?
        if len(self._skills_active) == 0:

            # Skills deactivated! Abort skills deactivation
            return

        # Check what event is fired
        if ev.name == 'player_death':

            # If player_death, died player might be NOT the owner
            if ev['userid'] == self.userid:

                # It's the owner. Deactivate
                self._skills_deactivate()

        elif ev.name == 'round_end':

            # Calculating values for round_end
            delay = other_functions.functions.skill_timings_calculate()

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

    def heal(self, hp: int, ignore_max=False) -> int:
        hp = hp * self.heal_multiplier

        # If ignoring max_hp, add all hp
        if ignore_max:
            self.health += int(hp)
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

        # If nothing above happened, healed hp will not be at max_health
        else:
            self.health += hp
            return hp

    def add_xp(self, amount: int, reason: str = None, divide: bool = True) -> None:

        # Getting skills amount
        skills_amount: int = len(self.skills_selected)

        # If no active skills, return
        if skills_amount == 0: return

        # User enabled xp notify?
        if self.data_info['xp_add_notify']:
            # Notifying player about added xp

            # No reason
            if reason is None:

                # Use string without reason
                SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 опыта").send(self.index)

            # Reason exist
            else:

                # Add reason in string
                SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 "
                         f"опыта за \5{reason}\1").send(self.index)

        # Amount of xp to add for each skill, if divide enabled
        if divide: amount: int = amount // skills_amount

        # Going through every skill
        for num, current_xp in enumerate(self.skills_selected_xp):

            # # May be there's no need for next 5 lines
            # # Breaking, if there's skill in current slot
            # if self.skills_selected[num] is None or \
            #         self.skills_selected[num] == 'Empty' or \
            #         self.skills_selected[num] == 'BLOCKED':
            #     continue

            # Checking, if in this slot skill is present
            if current_xp is None: continue

            # Adding xp
            self.skills_selected_xp[num] += amount

            # Variable to check, if skill leveled up by this xp
            leveled_up = False

            # Adding lvl, while there's enough xp
            while self.skills_selected_xp[num] > self.skills_selected_next_lvl[num]:

                # Leveled up?
                leveled_up = True

                # Adding lvl
                self.skills_selected_lvls[num] += 1

                # Adding +1 to overall lvls count
                self.total_lvls += 1

                # Subtracting xp, that needed to lvl up
                self.skills_selected_xp[num] -= self.skills_selected_next_lvl[num]

                # Setting new max_xp
                self.skills_selected_next_lvl[num] = \
                    next_lvl_xp_calculate(self.skills_selected_lvls[num])

                # Notifying player
                SayText2("\4[WCS]\1 Вы повысили уровень навыка "
                         f"\4{db.wcs.Skills_info.get_name(self.skills_selected[num])}\1 "
                         f"до \5{self.skills_selected_lvls[num]}\1").send(self.index)

                # Player enabled sound for every up?
                if self.data_info['sound_level_up_for_every_up']:

                    # Playing sound
                    self.emit_sound(f'{other_functions.constants.WCS_FOLDER}/level_up.mp3',
                        attenuation=1.1,
                        volume = 0.5)

            # Playing sound, if player enabled sounds and disabled sound for each
            if leveled_up and self.data_info['sound_level_up'] and not self.data_info[
                'sound_level_up_for_every_up']:

                # Playing sound
                self.emit_sound(f'{other_functions.constants.WCS_FOLDER}/level_up.mp3',
                    attenuation=1.1,
                    volume = 0.5
                )

    def add_level(self, amount: int, reason: str = None) -> None:

        # No reason
        if reason is None:

            # Use string without reason
            SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 уровней").send(self.index)

        # Reason exist
        else:

            # Add reason in string
            SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 "
                     f"уровней за \5{reason}\1").send(self.index)

        # Going through every skill
        for num, current_lvl in enumerate(self.skills_selected_lvls):

            # Checking, if slot is used to skill (not blocked, empty, e.t.c.)
            if current_lvl is None: continue

            # Adding lvl
            self.skills_selected_lvls[num] += amount

            # Adding +1 to player lvl count
            self.total_lvls += amount

            # Setting new max_xp
            self.skills_selected_next_lvl[num] = \
                next_lvl_xp_calculate(self.skills_selected_lvls[num])

    def add_level_to_bank(self, amount: int, reason: str = None) -> None:

        # No reason
        if reason is None:

            # Use string without reason
            SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 уровней в банк").send(self.index)

        # Reason exist
        else:

            # Add reason in string
            SayText2(f"\4[WCS]\1 Вы получили \5{amount}\1 "
                     f"уровней в банк за \5{reason}\1 ").send(self.index)

        # Adding levels to player bank
        self.lk_lvls += amount

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
        db.wcs.DB_users.info_save(self.steamid, [("total_lvls", self.total_lvls),
                                          ("skills_selected", f"{self.skills_selected}"),
                                          ("LK_lvls", self.lk_lvls)])
        db.wcs.DB_users.skills_save(self.steamid, self.data_skills)
        db.admin.DC_history.add_entry(self.name, self.steamid, self.address)

        # Logging
        WCSSkills.WCS_Logger.wcs_logger('player state', f"{self.name} WCS_Player unloaded")


# =============================================================================
# >> Other
# =============================================================================

# Checking if server is running on plugin load
if server.is_active():

    # If running, adding every player to WCS_Players set
    for player in PlayerIter():

        # Calling load function
        player_load({'userid': player.userid})