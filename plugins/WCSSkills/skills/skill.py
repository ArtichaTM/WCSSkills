# ../WCS/wcs/skills.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# Math
from random import randint
from math import sqrt
# typing
from typing import Iterable

# Source.Python Imports
# Entity
from entities.entity import Entity
from filters.entities import EntityIter
# Player
from players.entity import Player
# Weapon
from weapons.engines.csgo import Weapon
# Listeners
from listeners.tick import Delay
from listeners.tick import Repeat
from listeners import OnEntityOutputListenerManager
# Events
from events.manager import event_manager
from events.hooks import pre_event_manager
# Messages
from messages.base import SayText2 as ST2
# Models
from engines.precache import Model
# Colors
from colors import Color
# Enumeratings
from players.constants import PlayerButtons
from entities.constants import RenderMode
from entities.constants import EntityEffects
from entities.constants import MoveType
# Server
from engines.server import server
# Trace
from engines.trace import engine_trace
from engines.trace import ContentMasks
from engines.trace import GameTrace
from engines.trace import Ray
from engines.trace import TraceFilterSimple

# Plugin Imports
# Functions
from .functions import *
from ..other_functions.functions import *
# WCS_Player
from ..wcs.WCSP.wcsplayer import WCS_Player
# Effects
from ..other_functions.wcs_effects import effect, persistent_entity, Triggers
# Skills information
from ..db.wcs import Skills_info
# Constants
from ..other_functions.constants import WCS_DAMAGE_ID
from ..other_functions.constants import WCS_FOLDER
from ..other_functions.constants import weapon_translations
# Enumeratings
from ..other_functions.constants import DamageTypes
from ..other_functions.constants import ImmuneTypes
from ..other_functions.constants import ImmuneReactionTypes
from ..other_functions.constants import AffinityTypes


# =============================================================================
# >> ALL DECLARATION
# =============================================================================

__all__ = (
'Heal_per_step',  # Heals every step
'Start_add_speed',  # Adds speed after start of round
'Start_set_gravity',  # Adds gravity after start of round
'Long_jump' , # Boosts horizontal jump
'Regenerate',  # Default regeneration with intervals
'Health',  # Adds health after start of round
'Slow_fall',  # Slowing fall
'Nearly_Aim',  # Helps to aim, when user fires in body/legs/...
'Trigger',  # Fires when player comes into sight
'Start_add_max_hp',  # Adds max health after start of round
'Teleport',  # Teleports player
'Aim',  # Full aim from every angle, but with lower chances
'WalkOnAir',  # Allow player to walk on air and fire without distortion
'Poison',  # Poisons player with damage every second
'Ammo_gain_on_hit',  # Adds ammo on successful hit
'Additional_percent_dmg',  # Deals addition damage as magic
'Auto_BunnyHop',  # Allows players to auto jump with some limit
'Paralyze',  # Paralyze player on hit (with cd)
'Smoke_on_wall_hit',  # Instantly smoke when touch something
'Damage_delay_defend',  # Delays all physical damage
'Toss',  # Toss player in the air (with constants cd)
'Mirror_paralyze',  # Paralyze when being hit
'Vampire_damage_percent',  # Gives owner hp as percent of damage dealt
'Drop_weapon_chance',  # Drops enemy weapon with such chance
'Screen_rotate_attack',  # Rotates enemy screen with a chance
'MiniMap',  # Places minimap with player as orbs corresponding to their position
)


# =============================================================================
# >> Skills
# =============================================================================

class BaseSkill:
    """ Base abstract skill for all new skills """
    __slots__ = ('owner', 'lvl', 'settings', 'name', 'costs', '_efficiency')

    def __init__(self, userid: int, lvl: int, settings: dict, exclude_costs = True) -> None:
        """
        :param userid: Owner userid
        :param lvl: Current skill lvl
        :param settings: Current skill settings
        :param exclude_costs:
            True: Subtracts settings cost (where True) from self.lvl
            False: creates self.costs with settings dict {setting: bool}
        """

        # Saving owner
        self.owner: WCS_Player = WCS_Player.from_userid(userid)

        # Setting name of skill
        self.name = f"skill.{type(self).__name__}"

        # Getting skill maximum lvl
        max_lvl = Skills_info.get_max_lvl(self.name)

        # Getting settings
        self.settings = settings

        # Loading price for settings
        costs = Skills_info.get_settings_cost(self.name)

        # Exclude costs from self.lvl?
        if exclude_costs:

            # Subtract lvl for each setting
            for setting, value in self.settings.items():

                # If setting active
                if value is True:

                    # Will lvl go under 0?
                    if lvl - costs[setting] < 0:

                        # Cancel activation. Not enough levels
                        continue

                    # Subtracting it's cost
                    lvl -= costs[setting]

        # No, setting it to self.costs
        else: self.costs = costs

        # # Lvl limits check

        # Lvl equals -1 -> no limit to lvl
        if max_lvl == -1: self.lvl = lvl

        # Lvl above maximum -> Change lvl to max
        elif lvl > max_lvl: self.lvl = max_lvl

        # Lvl below minimum -> Change lvl to 0
        elif lvl < 0: self.lvl = 0

        # All is ok, set lvl as in arguments
        else: self.lvl = lvl

        # Setting efficiency to 1 (default)
        self._efficiency = 1

    def __repr__(self):
        return (f"{self.name}(lvl={self.lvl}, "
               f"settings={self.settings}, owner = {self.owner.__repr__()})")

    @property
    def efficiency(self) -> float:
        return self._efficiency

    @efficiency.setter
    def efficiency(self, value: float) -> None:
        self._efficiency = value

    def close(self) -> None:
        pass


class ActiveSkill(BaseSkill):
    """ Inherit this class, if u need to create ultimate/ability """
    __slots__ = ('delay', 'cd')

    def __init__(self, userid: int, lvl: int, settings: dict, exclude_costs = True):
        super().__init__(userid, lvl, settings, exclude_costs),

        # Adding skill to active skills class
        self.owner.Buttons.add_new_button(self)

        # Cooldown of skills (uses listeners.tick.Delay class)
        self.delay = None

    def bind_pressed(self) -> bool:
        """
        Triggered when active button pressed

        :return: Has cd passed?
        """

        if self.delay.running:
            ST2("\4[WCS]\1 Ещё не готово! Осталось "
            f"\5{self.delay.time_remaining:.1f}\1").send(self.owner.index)
            return False
        else:
            Delay(0.1, self.owner.Buttons.hud_update)
            return True

    def bind_released(self) -> bool:
        """
        Triggered when active button released
        :return: Has cd passed?
        """

        if self.delay.running:
            ST2("\4[WCS]\1 Ещё не готово! Осталось "
            f"\5{self.delay.time_remaining:.1f}\1").send(self.owner.index)
            return False
        else:
            Delay(0.1, self.owner.Buttons.hud_update)
            return True

    def cd_passed(self) -> None:
        self.owner.emit_sound(f'{WCS_FOLDER}/active_skill_ready')
        Delay(0, self.owner.Buttons.hud_update)


class PeriodicSkill(BaseSkill, repeat_functions):
    """ Inherit this skill, if u need to create poison, fire, e.t.c. """
    __slots__ = ('infect_dict',)

    def __init__(self, lvl: int, userid: int, settings: dict, exclude_costs = True):
        super().__init__(userid, lvl, settings, exclude_costs)

        # Dictionary that stores infected players
        self.infect_dict = dict()

        # How often call infect_activate and remove tokens?
        self.repeat_delay = 1

    def infect_activate(self) -> None:
        """ Adds tokens to victim """
        raise NotImplemented('infect_activate should be changed')

    def tick(self) -> None:
        """ Triggers to infected players every {repeat_delay} """

        for key in self.infect_dict:
            self._remove_token(key)

    def add_token(self, userid: int, amount: int = 1) -> None:
        """
        Adds tokens to userid

        :param userid: userid of victim
        :param amount: how many tokens to add

        """

        # Is player already under this periodic skill?
        if userid in self.infect_dict:

            # Yes, adding tokens
            self.infect_dict[userid] += amount

        else:

            # No, creating and add tokens
            self.infect_dict[userid]: int = amount

    def _remove_token(self, userid: int) -> None:

        # Getting amount of tokens
        tokens: int = self.infect_dict[userid]

        # Removing one
        tokens -= 1

        # All tokens used?
        if tokens == 0:

            # Remove user from dict
            self.infect_dict.pop(userid)

        # If not
        else:

            # Apply new value of tokens to him
            self.infect_dict[userid] = tokens

    def close(self) -> None:
        super().close()

        # Clearing dict on infected players
        self.infect_dict.clear()

        # Stop repeat
        self._repeat_stop()


class DelaySkill(BaseSkill):
    """ Inherit this skill, if u need to create skill with cooldown """
    __slots__ = ('cd', 'cd_length')

    def __init__(self, userid: int, lvl: int, settings: dict, exclude_costs = True):
        super().__init__(userid, lvl, settings, exclude_costs)

        # length of cd
        self.cd_length = 0

        # Delay
        self.cd = Delay(0, self.cd_passed)

        # Adding to buttons as delay skill
        self.owner.Buttons.add_new_skill(self)

    def cd_passed(self):
        pass


class AuraSkill(BaseSkill, repeat_functions):
    __slots__ = ('_victims', '_immune_type')

    def __init__(self, userid: int, lvl: int, settings: dict, exclude_costs = True) -> None:
        super().__init__(userid, lvl, settings, exclude_costs)

        # List of victims, that affected by aura
        self._victims = set()

        # repeat_functions initialize
        self.repeat = Repeat(self.check)

    def _players_list(self) -> Iterable:
        """
        :return: Iterable with players around owner
        """
        raise NotImplementedError("Implement players_list, that will return Iterable"
                                  "with players around owner")

    def check(self):
        """ Checks for players, that entered aura and left it """

        # Getting victims generator
        victims = self._players_list()

        # Converting to set
        victims = set(victims)

        # Finding differences
        left = victims.difference(self._victims)
        entered = self._victims.difference(victims)

        # Calling functions
        for value in left: self._left(value)
        for value in entered: self._entered(value)

        # Updating set (removing 'left' and adding 'entered')
        self._victims = self._victims.difference(left).union(entered)

    def deflect_function(self, deflector: WCS_Player) -> None:
        """ Called when player deflected aura """
        pass

    def _left(self, player: WCS_Player) -> None:
        """ Called with player, who left aura """
        pass

    def _entered(self, player: WCS_Player) -> None:
        """ Called with player, who entered aura """
        pass

    def close(self) -> None:
        super().close()


class Health(BaseSkill):
    """
    Skill, that adds hp (not max_health!) on spawn.
    Adds 1hp for each lvl

    Maximum lvl: 1000
    Maximum lvl skill power: +1000 hp
    """

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Adding health
        self.owner.heal(self.lvl, ignore_max = True)

        if self.owner.data_info['skills_activate_notify']:
            # Notifying player
            ST2(f"\4[WCS]\1 Вы получили \5{self.lvl}\1 к хп").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class Start_add_speed(BaseSkill):
    """
    Skill adds speed in the start of the round
    Each lvl increases speed by 1%

    Max lvl: 1000
    Max lvl skill: Speed increased by 1000%
    """

    __slots__ = ('speed',)

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Saving basic information into instance
        self.speed: int = self.lvl//5

        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            ST2("\4[WCS]\1 Ваша скорость увеличена на "
            f"\5{self.speed}\1%").send(self.owner.index)

        # Adding speed
        self.owner.speed += self.speed/100

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Removing added speed
        self.owner.speed -= self.speed/100


class Regenerate(BaseSkill, repeat_functions):
    __slots__ = ('interval', 'hp')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)


        # Checks for level for proper interval/radius/hp scaling

        # 901 -> infinity
        # Interval: 7
        # Hp:       Scaling from 100 to infinite with step 100
        if self.lvl > 900:
            self.interval = 7
            self.hp = 91 + self.lvl // 100

        # 11 -> 900
        # Interval: 7
        # Hp:       Scaling from 10 to 100 with step 10
        elif self.lvl > 10:
            self.interval = 7
            self.hp = 10 + self.lvl // 10

        # 0 -> 10
        # Interval: Scaling from 17 to 10 with step 1
        # Hp:       5
        else:
            self.interval = 17 - self.lvl
            self.hp = 10

        self.repeat = Repeat(self.heal)
        self.repeat_delay = self.interval
        self._repeat_start()

        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            ST2("\4[WCS]\1 Регенерация "
            f"\5{self.hp}\1хп/\5{self.interval}\1с").send(self.owner.index)

    def heal(self) -> None:
        healed: int = self.owner.heal(self.hp)
        if self.settings['notify'] and healed > 0:
            ST2(f"\4[WCS]\1 Вы исцелились на \5{healed}\1 "
                      "(регенерация)").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self._repeat_stop()


class Heal_per_step(BaseSkill):
    """
    Skill that heals several hp every "interval" step
    """
    __slots__ = ('hp', 'interval', 'counter')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Skill constants
        self.hp = 5
        if lvl <= 8:
            self.interval = 15 - lvl
        else:
            self.interval = 7
            self.hp += ((self.lvl-8)//30)
        self.counter = 0


        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            ST2(f"\4[WCS]\1 Вы исцеляетесь на \5{self.hp}\1хп "
            f"каждые \5{self.interval}\1 шагов").send(self.owner.index)

        # Register for footstep event
        event_manager.register_for_event('player_footstep', self.step)

    def step(self, ev) -> None:

        # Check if event is fired by owner of this skill
        if ev['userid'] == self.owner.userid:

            # Step counter
            self.counter+=1

            # If step count achieved "interval", activate heal, reset counter
            if self.counter == self.interval:

                # Resetting step counter
                self.counter = 0

                # Healing player
                healed = self.owner.heal(self.hp)

                # Notify, if player activated this in settings
                if self.settings['notify'] and healed > 0:
                    ST2("\4[WCS]\1 Вы исцелились на "
                    f"\5{healed}\1 за шаг").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregister from footstep event
        event_manager.unregister_for_event('player_footstep', self.step)


class Start_set_gravity(BaseSkill):
    """
    Skill reduces gravity at the start of round
    """
    __slots__ = ('grav',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        if self.lvl < 1000:
            self.grav = self.lvl / 1000

            # Adding gravity
            self.owner.gravity -= self.grav

            if self.owner.data_info['skills_activate_notify']:
                # Notifies player about perk activation
                ST2("\4[WCS]\1 Ваша гравитация уменьшена на "
                f"\5{self.grav*100}\1%").send(self.owner.index)
        else:
            self.owner.move_type = MoveType.FLY
            if self.owner.data_info['skills_activate_notify']:
                ST2(f"\4[WCS]\1 Ваша гравитация уменьшена на"
                "\5 100\1%").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        if self.lvl == 1000:
            self.owner.move_type = MoveType.WALK
        else:

            # Removing added gravity
            self.owner.gravity = 1


class Long_jump(BaseSkill):
    """
    Skill that speeds up player on jump

    Maximum lvl: 999
    Maximum lvl skill: Power of jump multiplied 100 times
    """
    __slots__ = ('power',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Saving basic information into instance
        if self.lvl: # self.lvl != 0
            self.power = self.lvl / 100
        else:
            self.power = 1

        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            ST2("\4[WCS]\1 Длина вашего прыжка увеличена в "
            f"\5{int(self.power)}\1 раз").send(self.owner.index)

        # Registration for player jump
        event_manager.register_for_event('player_jump', self.jump)

    def jump(self, ev) -> None:
        # Check if event is fired by owner of this skill
        if ev['userid'] == self.owner.userid:
            # TODO: property is broken. Always False
            # if self.owner.get_property_bool('m_bHasWalkMovedSinceLastJump'
            #     '') or self.settings['allow_bhop']:
                Delay(0, self.speed_up)

    def speed_up(self) -> None:
        vel = self.owner.velocity
        vel[0] = vel[0] * self.power
        vel[1] = vel[1] * self.power
        self.owner.teleport(velocity = vel)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        event_manager.unregister_for_event('player_jump', self.jump)


class Slow_fall(BaseSkill, repeat_functions):
    """
    Skill that allows soaring during fall.
    Works only if player jumped and begun falling.
    """
    __slots__ = ('limit',)

    fall_speed_list = ([i*5 for i in range(101,0,-1)])

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Saving information about owner and arg
        self.limit: int = self.fall_speed_list[self.lvl]

        # Repeat for fly
        self.repeat = Repeat(self.tick)

        # Notifies player about perk activation
        if self.owner.data_info['skills_activate_notify']:
            if self.limit == 5:
                ST2("\4[WCS]\1 Вы \5чрезвычайно\1 медленно "
                         "падаете").send(self.owner.index)
            elif self.limit <= 105:
                ST2("\4[WCS]\1 Вы \5значительно\1 медленнее "
                         "падаете").send(self.owner.index)
            elif self.limit <= 255:
                ST2("\4[WCS]\1 Вы \5умеренно\1 медленнее "
                         "падаете").send(self.owner.index)
            elif self.limit <= 405:
                ST2("\4[WCS]\1 Вы \5незначительно\1 медленнее "
                         "падаете").send(self.owner.index)
            else:
                ST2("\4[WCS]\1 Вы \5слегка\1 медленнее "
                         "падаете").send(self.owner.index)

        # Registration for jump
        event_manager.register_for_event('player_jump', self.activate_tick)

    def activate_tick(self, _) -> None:

        # Launching only if speed is normal
        if self.owner.speed <= 1: self._repeat_start()

    def tick(self) -> None:
        try:
            # If player ducking, abort soaring
            if self.owner.is_ducked and self.settings['ctrl_disable']:
                return
        except RuntimeError:
            self._repeat_stop()
            return

        # Picking player velocity Vector
        vel = self.owner.velocity

        # Picking difference between limit vel and player vel
        difference = self.owner.fall_velocity - self.limit

        # If difference bigger than zero, activating slow down...
        if difference > 0:

            # By the difference between them
            vel[2] += self.owner.fall_velocity - self.limit

            # Applying
            self.owner.teleport(velocity = vel)

        # If player landed, cancel OnTick listener
        if self.owner.ground_entity != -1:
            self._repeat_stop()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self._repeat_stop()


class Nearly_Aim(BaseSkill):
    """
    Some accuracy for shots. If player fired in body,
    aim in hed
    """
    __slots__ = ('back_to_aim', 'target_loc', 'angle')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.back_to_aim = False
        self.target_loc = None

        # Offset to hit head. Head hitbox is slightly displaced forward
        self.angle = 0.5

        # If player reached back_to_aim lvl, turn ON
        if self.lvl >= 500 and self.settings['back_to_aim']:
            self.back_to_aim = True

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Ваше оружие модифицировано \5доводкой\1").send(self.owner.index)

            if self.settings['headshot']:
                ST2(f"\4[WCS]\1 Шанс попасть в голову: \5{self.lvl/10}%\1").send(self.owner.index)
            if self.settings['back_to_aim']:
                ST2("\4[WCS]\1 Вернуть прицел после выстрела: "
                f"\5{'вкл' if self.back_to_aim == True else 'выкл'}\1").send(self.owner.index)

        # Register for firing
        pre_event_manager.register_for_event('weapon_fire', self.fire)

    def fire(self, event) -> None:
        if event['userid'] != self.owner.userid:
            return
        if self.owner.view_player is not None and self.lvl >= randint(0,100):
            target = self.owner.view_player
            self.target_loc = self.owner.view_coordinates
            if self.settings['headshot']:
                target_loc = target.eye_location
                target_loc[2] += 0.1
                if self.lvl >= randint(0,1001):
                    distance = target.origin.get_distance(target.view_coordinates)
                    origin = target.origin
                    for num in range(0,3):
                        origin[num] -= target.view_coordinates[num]
                    for num in range(0,2):
                        if target.team == 2:
                            target_loc[num] -= (origin[num]/distance)*5
                        else:
                            target_loc[num] -= (origin[num]/distance)*10
                else:
                    if self.settings['only_headshot']:
                        return
                    target_loc[2] -= 10


                self.owner.view_coordinates = target_loc
                if self.back_to_aim:
                    Delay(0, self.back)
            else:
                target_loc = target.eye_location
                target_loc[2] -= 10

                self.owner.view_coordinates = target_loc
                if self.back_to_aim:
                    Delay(0, self.back)

    def back(self) -> None:
        self.owner.view_coordinates = self.target_loc

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        pre_event_manager.unregister_for_event('weapon_fire', self.fire)


class Trigger(ActiveSkill):
    __slots__ = ('cd', 'length', 'is_pressed', 'repeat')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.cd = 50 - (self.lvl/25)
        self.length = 2
        # self.length = self.lvl/100
        self.is_pressed = False

        self.delay = Delay(self.cd*2, self.cd_passed)

    def bind_pressed(self) -> None:
        if self.delay.running:
            ST2("\4[WCS]\1 Ещё не готово! Осталось "
            f"\5{self.delay.time_remaining:.1f}\1").send(self.owner.index)

        # noinspection PyAttributeOutsideInit
        self.repeat = Repeat(self.tick)
        self.repeat.start(0)
        self.is_pressed = True
        Delay(self.length, self.bind_released)
        if self.settings['activate_notify']:
            ST2(f"\4[WCS]\1 Триггер \2активирован\1")

    def bind_released(self) -> None:
        if self.is_pressed:
            self.repeat.stop()
            self.delay = Delay(self.cd, self.cd_passed)
            self.is_pressed = False
            if self.settings['activate_notify']:
                ST2(f"\4[WCS]\1 Триггер \7деактивирован\1")

    def tick(self) -> None:
        target = self.owner.view_player
        if target is not None:
            force_buttons(self.owner, PlayerButtons.ATTACK)

    def cd_passed(self) -> None:
        ST2(f"\5[WCS]\1 Триггер \5готов\1").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class Start_add_max_hp(BaseSkill):

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.owner.max_health += self.lvl//2

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Ваше максимальное здоровье увеличено"
            f" на \4{self.lvl//2}\1").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class Teleport(ActiveSkill):
    __slots__ = ('position', 'cd', 'allowed_distance', 'is_pressed')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Position, where player will be teleported after button release
        self.position = None
        self.cd = 30 - (self.lvl/100)
        self.allowed_distance = 100 + lvl
        self.delay = Delay(self.cd, self.cd_passed)
        self.is_pressed = False

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Телепорт радиусом "
            f"\5{self.allowed_distance}\1 юнитов активирован").send(self.owner.index)

    def bind_pressed(self) -> None:

        # Get destination coordinates
        self.position = self.owner.eye_location + self.owner.view_vector * self.allowed_distance

        # Player on ground?
        if self.owner.ground_entity == -1:
            # Then destination calculates from eyes

            # Setting ray from player toes to destination
            ray = Ray(self.owner.origin, self.position, self.owner.mins, self.owner.maxs)

        else:
            # Then destination calculates from origin

            # Setting ray from player eyes to destination
            ray = Ray(self.owner.eye_location, self.position, self.owner.mins, self.owner.maxs)

        # Setting trace instance
        trace = GameTrace()

        # Tracing to destination
        engine_trace.trace_ray(ray, ContentMasks.ALL, TraceFilterSimple((self.owner,)), trace)

        # If hit something, set pre-hit position as destination
        if trace.did_hit():  self.position = trace.end_position

        # Marking press
        self.is_pressed = True

    def bind_released(self) -> None:

        # Marking release
        self.is_pressed = False

        # Cooldown passed?
        if super().bind_released():

            # Teleporting player
            self.owner.teleport(self.position)

            # Clearing position
            self.position = None

            # Emit sound
            self.owner.emit_sound(f'{WCS_FOLDER}/skills/Teleport/success.mp3',
                                  attenuation = 0.8)

            # Starting cooldown
            self.delay = Delay(self.cd//2, self.cd_passed)

    def cd_passed(self) -> None:
        ST2(f"\4[WCS]\1 Телепорт \5готов\1").send(self.owner.index)
        if self.is_pressed is True and self.settings['after_cd_instantly']:
            self.bind_released()

    def close(self) -> None:
        if self.delay.running is True:
            self.delay.cancel()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class Aim(BaseSkill):

    __slots__ = ('back_to_aim', 'target_loc')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.back_to_aim = False
        self.target_loc = None
        if self.lvl >= 1000 and self.settings['back_to_aim']:
            self.back_to_aim = True
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Ваше оружие модифицировано \5наводкой\1").send(self.owner.index)
            ST2(f"\4[WCS]\1 Шанс наводки: \5{self.lvl/15:.0f}%\1").send(self.owner.index)

            if self.settings['headshot']:
                ST2(f"\4[WCS]\1 Шанс попасть в голову: \5{self.lvl/100:.0f}%\1").send(self.owner.index)

            if self.settings['back_to_aim'] and lvl >= 1000:
                ST2("\4[WCS]\1 Вернуть прицел после выстрела: "
                f"\5{'включено' if self.back_to_aim == True else 'выключено'}\1"
                ).send(self.owner.index)

        pre_event_manager.register_for_event('weapon_fire', self.fire)

    def fire(self, ev) -> None:
        # Canceling if activated not by owner
        if ev['userid'] != self.owner.userid:
            return

        # Aborting, if chance not worked
        if not chance(self.lvl, 1500):
            return

        # Looking for player
        target = open_players(entity=self.owner,
                              form = ImmuneTypes.Default,
                              only_one = True,
                              type_of_check='aimbot')

        # If found, and chance worked
        if target:
            target = target[0]
            self.target_loc = self.owner.view_coordinates
            if self.settings['headshot']:
                target_loc = target.eye_location
                target_loc[2] += 0.1
                if chance(self.lvl, 10000):
                    origin_normalized = (target.origin - target.view_coordinates).normalized()
                    for num in range(0,2):
                        if target.team == 2:
                            target_loc[num] -= origin_normalized[num]*5
                        else:
                            target_loc[num] -= origin_normalized[num]*10
                else:
                    if self.settings['only_headshot']:
                        return
                    target_loc[2] -= 10


                self.owner.view_coordinates = target_loc
                if self.back_to_aim:
                    Delay(0, self.back)
            else:
                target_loc = target.eye_location
                target_loc[2] -= 10

                self.owner.view_coordinates = target_loc
                if self.back_to_aim:
                    Delay(0, self.back)

    def back(self) -> None:
        self.owner.view_coordinates = self.target_loc

    def close(self) -> None:
        super().close()
        pre_event_manager.unregister_for_event('weapon_fire', self.fire)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class WalkOnAir(ActiveSkill):
    __slots__ = ('model', 'is_active', 'cd', 'repeat', 'entity')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings),
        self.model = Model('models/props/cs_italy/orange.mdl')
        Model('models/props/cs_italy/orangegib1.mdl')
        Model('models/props/cs_italy/orangegib2.mdl')
        Model('models/props/cs_italy/orangegib3.mdl')

        if not self.settings['hold']:
            self.is_active = False
        self.cd = 101 - self.lvl/10
        self.delay = Delay(self.cd, self.cd_passed)
        self.repeat = Repeat(self.tick)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Вы можете \5ходить по воздуху\1").send(self.owner.index)

    def _create_prop(self) -> None:
        self.entity = Entity.create('prop_physics')
        self.entity.model = self.model
        self.entity.effects = EntityEffects.NOSHADOW | EntityEffects.NORECEIVESHADOW
        self.entity.render_color = Color(255, 255, 255, 0)
        self.entity.render_mode = RenderMode.TRANS_ALPHA
        self.entity.spawn()

        position = self.owner.origin
        position[2]-=8.2
        self.entity.origin=position

        # Setting entity settings
        self.entity.health = 10000
        self.entity.set_datamap_property_int("m_MoveType", 0)
        self.entity.set_datamap_property_float('m_flModelScale', 0.01)

        self.owner.emit_sound(f'{WCS_FOLDER}/skills/WalkOnAir/'
                              f'success.mp3', attenuation=0.8)

    def bind_pressed(self) -> None:
        if super().bind_pressed():
            if self.settings['hold']:
                self._create_prop()
                self.repeat.start(0)
            else:
                if self.is_active:
                    self.repeat.stop()
                    self.entity.remove()
                    self.delay = Delay(self.cd/2, self.cd_passed)
                    self.is_active = False
                else:
                    self._create_prop()
                    self.repeat.start(0)
                    self.is_active = True

    def bind_released(self, remove = True) -> None:
        if not self.delay.running and self.settings['hold']:
            self.repeat.stop()
            self.entity.remove()
            self.delay = Delay(self.cd/2, self.cd_passed)

    def tick(self) -> None:
        position = self.owner.origin
        if self.owner.ground_entity == -1:
            position[2]-=8.3
        else:
            position[2] = self.entity.origin[2]
        self.entity.origin=position

    def close(self) -> None:
        super().close()
        if self.repeat.status == 2:
            self.repeat.stop()
            self.entity.remove()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class Poison(PeriodicSkill):
    __slots__ = ('chance', 'dmg', 'length')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)
        self.chance = self.lvl/30
        self.length = 1 + self.lvl // 100
        self.dmg = self.length//2
        self.repeat_delay = 1

        self.repeat = Repeat(self.tick)
        event_manager.register_for_event('player_hurt', self.infect_activate)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Шанс \5{self.chance:.0f}%\1 отравить "
            f"противника на \5{self.length}\1 секунд "
            f"с \5{self.dmg}\1 уроном в секунду").send(self.owner.index)

    def infect_activate(self, ev=None) -> None:
        if ev['weapon'] == 'worldspawn':
            return

        # Aborting, if chance not worked
        if not chance(self.lvl, 100):
            return

        # If attack was from owner of this skill
        if ev['attacker'] == self.owner.userid:

            # Getting victim userid
            userid = ev['userid']

            # Adding token to him
            self.add_token(userid, self.length)

            # Starting infect repeat
            self._repeat_start()

            # Getting attacker Player class
            attacker = WCS_Player.from_userid(userid)

            # Notifying owner about infect
            ST2(f"[\4[WCS]\1 Вы заразили {attacker.name}").send(self.owner.index)

    def tick(self) -> None:
        super().tick()

        for iterations, userid in enumerate(self.infect_dict.copy()):
            victim = WCS_Player.from_userid(userid)
            victim.take_damage(
                damage = self.dmg,
                damage_type = WCS_DAMAGE_ID|DamageTypes.ACID,
                attacker_index = self.owner.index)
            tokens = self.infect_dict[userid]
            tokens -= 1

            if victim.dead:
                self.infect_dict.pop(userid)

        # If there's no victims left in dict, abort poison
        if len(self.infect_dict) == 0:
            self._repeat_stop()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self._repeat_stop()
        event_manager.unregister_for_event('player_hurt', self.infect_activate)


class Ammo_gain_on_hit(BaseSkill, repeat_functions):
    __slots__ = ('chance', 'amount', 'ammo_added')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)
        self.chance = self.lvl
        self.amount = self.lvl//100
        self.ammo_added = dict()
        self.repeat = Repeat(self.ammo_decay)
        self.repeat_delay = 4

        # Register for on_take_damage PreHook
        on_take_physical_damage.add(self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            if self.lvl >= 100:
                ST2(f"\4[WCS]\1 При попадание восполняется \5{self.amount}\1 "
                "патрон").send(self.owner.index)
            else:
                ST2(f"\4[WCS]\1 При попадание восполняется \5{self.amount}\1 "
                    f"патрон с шансом \5{self.chance}%\1").send(self.owner.index)

    def add_ammo(self, weapon) -> None:
        self._repeat_start()
        try:
            if weapon.clip > 200: return
        except ValueError: return
        weapon.clip += self.amount

        if weapon in self.ammo_added:
            self.ammo_added[weapon] += self.amount - 1
        else:
            self.ammo_added[weapon] = self.amount - 1

    def player_hurt(self, owner, info) -> bool:

        # Looking for attacker
        try: attacker = WCS_Player.from_index(info.attacker)

        # Attacker is not WCS_Player
        except KeyError: return True

        # Attacker is not Player (this happens)
        except ValueError: return True

        # Check if attacker has this perk
        if attacker.index != self.owner.index or \
            owner.team_index == attacker.team_index:
            return True

        if chance(self.chance, 100):
            self.add_ammo(Weapon(info.weapon))

        return True

    def ammo_decay(self):
        for weapon in self.ammo_added.copy():
            added: int = self.ammo_added[weapon]
            difference = weapon.clip - added//4
            if difference < 0:
                return
            weapon.clip = difference
            added = self.ammo_added[weapon] = added - added//4

            if added < 10:
                try:
                    weapon.clip -= added
                except OverflowError:
                    pass
                self.ammo_added.pop(weapon)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self):
        super().close()
        self._repeat_stop()
        on_take_physical_damage.remove(self.player_hurt)


class Additional_percent_dmg(BaseSkill):
    __slots__ = ('percent',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Amount of additional dmg
        self.percent: float = (self.lvl//10)/100

        # Adding to dmg function
        on_take_physical_damage.add(self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Вы наносите на \5{self.percent*100:.0f}%\1"
            " больше урона").send(self.owner.index)

    def player_hurt(self, entity, info) -> bool:
        # Enter data
        try: attacker = WCS_Player.from_index(info.attacker)
        except KeyError: return True
        except ValueError: return True

        player = Player(entity.index)

        # Check if attacker has this perk
        if attacker is None or attacker.index != self.owner.index:
            return True

        # Calculating additional damage
        add_damage: float = info.damage*self.percent

        # Applying
        info.damage += add_damage

        # Sound
        self.owner.emit_sound(f'{WCS_FOLDER}/skills/Additional_percent_dmg/'
                              f'success.mp3', Atenuation=0.8)

        # Notifying player about damage
        if self.settings['damage_notify']:
            ST2(f"\4[WCS]\1 Вы нанесли \5{add_damage:.0f}\1 доп "
            f"урона игроку \5{player.name:.10}\1").send(self.owner.index)

        return True

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self):
        super().close()
        on_take_physical_damage.remove(self.player_hurt)


class Auto_BunnyHop(BaseSkill, repeat_functions):
    __slots__ = ('hops', 'current_hops')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.hops = self.lvl // 10
        self.current_hops = 0
        self.repeat = Repeat(self.tick)
        self.repeat_delay = 0

        event_manager.register_for_event('player_jump', self.jumped)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Распрыжка на \5{self.hops}\1 прыжков").send(self.owner.index)

    def jumped(self, ev):
        if ev['userid'] == self.owner.userid:
            self._repeat_start()

    def tick(self):
        if self.owner.ground_entity != -1:
            if self.owner.get_property_int('m_nButtons') & PlayerButtons.JUMP:

                # If maximum bunnyhop jumps exceeded, abort
                if self.current_hops > self.hops:
                    self.current_hops = 0
                    self._repeat_stop()
                    return

                # Disabling jump button
                self.owner.set_datamap_property_int(
                    'm_Local.m_nOldButtons',
                    self.owner.get_datamap_property_int('m_Local.m_nOldButtons') & ~PlayerButtons.JUMP)

                # Marking, that jump is performed
                self.current_hops += 1

                # Fix for multiple applying
                self._repeat_stop()
                Delay(0.3, self._repeat_start)
            else:
                self.current_hops = 0
                self._repeat_stop()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self._repeat_stop()
        event_manager.unregister_for_event('player_jump', self.jumped)


class Paralyze(DelaySkill):
    __slots__ = ('length',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        if self.lvl == 0:
            self.lvl = 1

        self.length: float = self.lvl**0.2
        self.cd_length: float = self.lvl**-0.3*100

        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Паралич на \5{self.length:.1f}\1с "
            f"откатом в \5{self.cd_length:.1f}\1с").send(self.owner.index)

    def player_hurt(self, ev) -> None:

        attacker = WCS_Player.from_userid(ev['attacker'])
        victim = WCS_Player.from_userid(ev['userid'])

        # Abort, if attacker/victim is not WCS_Player
        if attacker is None or victim is None: return

        # Activating only if attacker was owner of this skill
        # and skill isn't on cooldown
        if attacker != self.owner or self.cd.running is True:
            return

        result = paralyze(
            owner = self.owner,
            victim = victim,
            length = self.length,
            form = ImmuneTypes.Default
            )

        # Beam effect
        effect.beam_laser(
            users=player_indexes(),
            start=self.owner.eye_location,
            end=attacker.view_coordinates,
            lifetime=1.5,
            width=3,
            amplitude=0,
            red=0,
            green=200,
            blue=0,
            a=150)

        # Notifying
        if result == ImmuneReactionTypes.Passed:

            # Victim
            ST2(f"\4[WCS]\1 Вас парализовал \5{self.owner.name:.10}\1 "
                     f"на \5{self.length:.1f}\1с").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Вы парализовали игрока \5"
                    f"{victim.name:.10}\1").send(self.owner.index)

        elif result == ImmuneReactionTypes.Immune:

            # Victim
            ST2("\4[WCS]\1 Вы защитились от паралича игрока \5"
                f"{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 У игрока \5{victim.name:.10}\1 "
                    f"защита от паралича").send(self.owner.index)

            return

        elif result == ImmuneReactionTypes.Deflect:

            # Victim
            ST2(f"\4[WCS]\1 Вы отразили паралич игрока \5"
                f"{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Игрок \5{victim.name:.10}\1"
                    f" отразил паралич").send(self.owner.index)

            return

        self.cd = Delay(self.cd_length, self.cd_passed)

    def cd_passed(self):
        if self.settings['cooldown_pass notify']:
            ST2(f"\4[WCS]\1 Паралич \5готов\1").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class Smoke_on_wall_hit(BaseSkill):

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)
        if self.lvl != 0:

            # Registering for bounce event
            event_manager.register_for_event('grenade_bounce', self.grenade_bounce)

            # Notifying player
            if self.owner.data_info['skills_activate_notify']:
                ST2("\4[WCS]\1 Ваш смок появится при первом соприкосновении "
                         "со стенкой/полом/потолком").send(self.owner.index)

    def grenade_bounce(self, ev):
        if ev['userid'] == self.owner.userid:
            for ent in EntityIter():
                if ent.class_name == 'smokegrenade_projectile':
                    index = ent.get_datamap_property_short('m_hThrower')
                    if index == self.owner.index:
                        ent.detonate()

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        if self.lvl != 0:
            event_manager.unregister_for_event('grenade_bounce', self.grenade_bounce)


class Damage_delay_defend(BaseSkill):
    __slots__ = ('damage_list', 'delay_length')

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # List with damages. How it looks like:
        # [(damage, type, attacker_index, weapon_index), ...]
        self.damage_list = []

        # How many time to delay
        self.delay_length = self.lvl / 1000

        # Adding to otd hook
        on_take_physical_damage.add(self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Урон по вам задержится на "
                     f"\5{self.delay_length:.1f}\1с").send(self.owner.index)

    def player_hurt(self, victim, info) -> bool:
        if victim.index == self.owner.index:

            # Adding data to list
            self.damage_list.append((
                info.damage,
                info.type,
                info.attacker,
                info.weapon
            ))

            # Delaying damage
            Delay(self.delay_length, self.damage)

            # Declining instant damage
            return False

    def damage(self):

        # Trying to get damage info
        try:

            # Getting info from list
            info = self.damage_list.pop(0)

        # Failed. List is empty. (May be skills deactivated during delay)
        except IndexError:

            # Aborting dealing damage
            return

        # Dealing damage
        self.owner.take_damage(

            # Damage (float)
            damage=info[0],

            # Type of damage + magic damage
            type=info[1]|WCS_DAMAGE_ID,

            # Index of attacker, to add kills
            attacker_index=info[2],

            # Index of weapon
            weapon_index=info[3]
        )

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Removing list with delays
        self.damage_list.clear()

        # Remove from otd hook
        on_take_physical_damage.remove(self.player_hurt)


class Toss(DelaySkill):
    __slots__ = ('chance', 'power')

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Calculating chance
        self.chance = sqrt(self.lvl)

        # Calculating power of toss
        self.power = self.lvl/10

        # Length of cd
        self.cd_length = 2

        # Registering for hurt event
        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 С шансом \5{self.chance:.0f}\1% вы подкинете "
                     f"противника с силой в \5{self.power:.0f}\1"
                     " юнитов").send(self.owner.index)

    def player_hurt(self, ev):

        # Event fired by player?
        if ev['attacker'] != self.owner.userid or self.cd.running is True:
            return

        # Getting weapon type
        weapon = ev['weapon']

        # Checking if weapon is inferno
        if (weapon == 'ainferno' or weapon == 'inferno') \
                and not self.settings['allow_inferno']: return

        # Checking, if weapon is he grenade
        if weapon == 'hegrenade' and not self.settings['allow_he']: return

        # Chance check
        if not chance(self.chance, 100): return

        # Getting victim
        try: victim = WCS_Player.from_userid(ev['attacker'])

        # No such WCS_Player?
        except KeyError:

            # Then it's 100% bot
            return

        result = throw_player_upwards(
            owner = self.owner,
            victim = victim,
            power = self.power,
            form = ImmuneTypes.Default )

        # Notifying
        if result == ImmuneReactionTypes.Passed:

            # Victim
            ST2(f"\4[WCS]\1 Вас подбросил \5{self.owner.name:.10}\1"
                     '').send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Вы подбросили игрока \5"
                    f"{victim.name:.10}\1").send(self.owner.index)

        elif result == ImmuneReactionTypes.Immune:

            # Victim
            ST2("\4[WCS]\1 Вы защитились от подбрасывания игрока "
                f"\5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 У игрока \5{victim.name:.10}\1 "
                    f"защита от подбрасывания").send(self.owner.index)

        elif result == ImmuneReactionTypes.Deflect:

            # Victim
            ST2(f"\4[WCS]\1 Вы отразили подбрасывание игрока \5"
                f"{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Игрок \5{victim.name:.10}\1"
                    f" отразил подбрасывание").send(self.owner.index)

        # Player disabled no_cd?
        if not self.settings['no_cd']:

            # Launching cooldown
            self.cd = Delay(1, self.cd_passed)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregistering for hurt event
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class Mirror_paralyze(BaseSkill):
    __slots__ = ('chance', 'length')

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Setting chance of skill
        self.chance = self.lvl / 100 + 1

        # Length of paralyze
        self.length: float = self.lvl ** 0.2 + 0.5

        # Registering for player_hurt
        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 С шансом \5{self.chance:.0f}\1% "
                     "вы парализуете противника при защите на "
                     f"\5{self.length:.1f}\1c").send(self.owner.index)

    def player_hurt(self, ev) -> None:

        # Is our user attacked?
        if ev['victim'] != self.owner.userid:
            return

        # Chance check
        if not chance(self.chance, 150):
            return

        # Getting attacker
        try: victim = WCS_Player.from_userid(ev['attacker'])

        # No such WCS_Player?
        except KeyError:

            # Then it's 100% bot. Abort. No mirror paralyze on bots :D
            return

        result = paralyze(
            owner = self.owner,
            victim = victim,
            length = self.length,
            form = ImmuneTypes.Default
            )

        # Notifying
        if result == ImmuneReactionTypes.Passed:

            # Victim
            ST2(f"\4[WCS]\1 Вас парализовали \5{self.owner.name:.10}\1 "
                     f"на \5{self.length:.1f}\1с").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Вы парализовали игрока \5"
                    f"{victim.name:.10}\1").send(self.owner.index)

        elif result == ImmuneReactionTypes.Immune:

            # Victim
            ST2("\4[WCS]\1 Вы защитились от паралича игрока \5"
                f"{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 У игрока \5{victim.name:.10}\1 "
                    f"защита от паралича").send(self.owner.index)

        elif result == ImmuneReactionTypes.Deflect:

            # Victim
            ST2(f"\4[WCS]\1 Вы отразили паралич игрока \5"
                f"{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Игрок \5{victim.name:.10}\1"
                    f" отразил паралич").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregistering from player_hurt
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class Vampire_damage_percent(BaseSkill):
    __slots__ = ('vampire_percent', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Percent. How many to heal
        self.vampire_percent = self.lvl / 10000 + 0.1

        # Register for player_hurt
        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Вы исцеляете \5{self.vampire_percent*100:.0f}\1%"
                     f" здоровья от урона по врагу").send(self.owner.index)

    def player_hurt(self, ev):

        # Checking, if attack did by owner
        if ev['attacker'] != self.owner.userid:
            return

        # Calculating amount to heal
        amount_to_heal = ev['dmg_health'] * self.vampire_percent

        # Healing, and stores healed hp
        healed = self.owner.heal(int(amount_to_heal))

        # Notifying owner
        if self.settings['hit notify'] and healed > 0:
            ST2(f"\4[WCS]\1 Вы исцелились на \5{healed}"
                     '\1 хп').send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregister from player_hurt
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class Drop_weapon_chance(BaseSkill):

    __slots__ = ('chance', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Setting chance of skill
        self.chance = self.lvl / 100 + 1

        # Register for hit
        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Вы выбросите оружие противника с шансом"
                     f"\5{self.chance:.1f}%\1").send(self.owner.index)

    def player_hurt(self, ev):

        # Attacker == Owner check
        if ev['attacker'] != self.owner.userid: return

        # Chance check
        if not chance(self.chance, 100): return

        # Getting victim
        try: victim = WCS_Player.from_userid(ev['userid'])
        except KeyError: return

        # Using weapon_drop function
        result = active_weapon_drop(
            owner = self.owner,
            victim = victim,
            form = ImmuneTypes.Default)

        # Notifying
        if result == ImmuneReactionTypes.Passed:

            # Victim
            ST2(f"\4[WCS]\1 \5{self.owner.name:.10}\1 "
                 f"выбросил ваше оружие").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Вы выбросили оружие игрока "
                         f"\5{victim.name:.10}\1").send(self.owner.index)

        elif result == ImmuneReactionTypes.Immune:

            # Victim
            ST2(f"\4[WCS]\1 Вы защитились выброса оружия "
                 f"игрока \5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 У игрока \5{victim.name:.10}\1 "
                         f"защита от выброса оружие").send(self.owner.index)

        elif result == ImmuneReactionTypes.Deflect:

            # Victim
            ST2(f"\4[WCS]\1 Вы отразили выброс оружия "
                 f"игрока \5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Игрок \5{victim.name:.10}\1 "
                         f"отразил выброс оружия").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregister from hit
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class Screen_rotate_attack(DelaySkill):

    __slots__ = ('distortion', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Amount to distort
        self.distortion = sqrt(self.lvl)

        self.cd_length = 2

        # Register for hit
        event_manager.register_for_event('player_hurt', self.player_hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Вы разворачиваете экран противника на"
                     f"\5{self.distortion:.0f}°\1").send(self.owner.index)

    def player_hurt(self, ev):

        # Attacker == Owner check
        if ev['attacker'] != self.owner.userid: return

        if self.cd.running is True: return

        # Getting victim
        try: victim = WCS_Player.from_userid(ev['userid'])
        except KeyError: return

        # Using distortion function
        result = screen_angle_distortion(
            owner = self.owner,
            victim = victim,
            form = ImmuneTypes.Default,
            amount = self.distortion)

        # Starting delay
        self.cd = Delay(self.cd_length, self.cd_passed)


        # Notifying
        if result == ImmuneReactionTypes.Passed:

            # Victim
            ST2("\4[WCS]\1 Ваш экран повернул игрок "
                 f"\5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Вы повернули экран "
                         f"\5{victim.name:.10}\1").send(self.owner.index)

        elif result == ImmuneReactionTypes.Immune:

            # Victim
            ST2(f"\4[WCS]\1 Вы защитились поворота экрана "
                 f"игрока \5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 У игрока \5{victim.name:.10}\1 "
                     f"защита от поворота экрана").send(self.owner.index)

        elif result == ImmuneReactionTypes.Deflect:

            # Victim
            ST2(f"\4[WCS]\1 Вы отразили поворот экрана "
                 f"игрока \5{self.owner.name:.10}\1").send(victim.index)

            # Owner
            if self.settings['hit notify']:
                ST2(f"\4[WCS]\1 Игрок \5{victim.name:.10}\1 "
                     f"отразил поворота экрана").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregister from hit
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class HE_Bloodhound(BaseSkill):

    __slots__ = ('power', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Calculating velocity multiplier
        self.power = sqrt(self.lvl)

        # Registering for bounce event
        event_manager.register_for_event('grenade_bounce', self.check)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Ваши HE-гранаты отскакивают в противника"
                f" с силой {self.power:.0f}°").send(self.owner.index)

    def check(self, _):

        # Delay to make grenade move from wall
        # This made for make rays didn't hit wall, that
        # grenade bouncing from
        Delay(0.1, self._check)

    def _check(self):

        for grenade in EntityIter(class_names=('hegrenade_projectile',)):

            # Getting thrower index
            thrower_index = grenade.get_property_short('m_hThrower')

            # Checking if it matches owner index
            if thrower_index != self.owner.index: continue

            # Looking for players
            victim = open_players(
                entity = grenade,
                form = ImmuneTypes.Penetrate,
                type_of_check = 'custom_aim',
                only_one = True
            )

            # Getting victim
            if len(victim) == 0: return
            else: victim = victim[0]

            # Applying velocity to this player
            velocity = victim.eye_location - grenade.origin
            velocity *= self.power

            # Add new velocity to old
            velocity += grenade.velocity

            if velocity.length < 150:

                # Detonate
                grenade.set_property_int('m_nNextThinkTick', server.tick + 1)

                # Abort function
                return

            # Applying velocity to the grenade
            grenade.teleport(velocity=velocity)

            # Adding -1 to ThinkTick, to delay his detonate
            grenade.set_property_int('m_nNextThinkTick', -1)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregistering from bounce event
        event_manager.unregister_for_event('grenade_bounce', self.check)


class Attack_dodge(BaseSkill):

    __slots__ = ('chance', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Saving chance
        self.chance = sqrt(self.lvl)

        # Registering for dmg
        on_take_physical_damage.add(self.hurt)

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 \5{self.chance:.0f}%\1 шанс увернуться "
                 "от атаки противника").send(self.owner.index)

    def hurt(self, victim, info) -> bool:

        ST2(f"Начало").send()

        # Abort if hurt not owner
        if victim.index != self.owner.index:
            ST2('Не наш игрок').send()
            return True

        ST2(f"Дошёл1").send()

        # Abort, if chance return False
        if not chance(self.chance, 100):
            ST2(f"Шанс не прокнул").send()
            return True

        ST2(f"Дошёл").send()

        # Getting attacker view_vector
        attacker_view = Player.from_userid(info.attacker).view_vector

        # Making perpendicular vector
        attacker_view[0], attacker_view[1] = attacker_view[1], attacker_view[2]

        # No changes in vertical dimension
        attacker_view[2] = 5

        # Negates any dimension, depending what we want
        for x_multiplier, y_multiplier in ((1, -1), (-1, 1)):

            # Negates some dimension + adding distance
            attacker_view[0] = attacker_view[0] * x_multiplier + 50
            attacker_view[1] = attacker_view[1] * y_multiplier + 50

            # Adding player origin
            attacker_view += self.owner.origin

            # If player stuck after teleport, continue iteration
            if will_be_stuck(self.owner, attacker_view): continue

            # Otherwise everything is OK
            else:

                # Teleport owner to a new position
                self.owner.teleport(origin = attacker_view)

                # And finalize function
                return False

        # If no 'break' called, notify owner about evade fail
        else:
            if self.settings['fail notify']: ST2('Уворот не удался').send()

        # Always return bool
        return True

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Unregistering for dmg
        on_take_physical_damage.remove(self.hurt)


class Weapon_give_start(BaseSkill):

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings, exclude_costs=False)

        # How much money owner has?
        money = self.lvl if self.lvl > 500 else 500

        # Set, that store all provided weapons
        weapons = set()

        # Iterating over all weapons, and trying to buy them
        for weapon, cost in self.costs.items():

            if self.settings[weapon] is False: continue

            # Go to the next cycle, if not enough money to buy
            if cost > money: continue

            # Buy, if enough
            else:

                # Give item to owner
                self.owner.give_named_item(weapon)

                # Add this weapon translation to provided set
                weapons.add(weapon_translations[weapon].lower())

                # Subtract cost from money
                money -= cost

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            if not weapons:
                ST2(f"\4[WCS]\1 Вы не выбрали оружия для выдачи, "
                    f"всего денег: \5{money}$\1").send(self.owner.index)
            elif len(weapons) == 1:
                ST2(f"\4[WCS]\1 Вам выдали \5{next(iter(weapons))}\1, "
                    f"у вас осталось \5{money}$\1").send(self.owner.index)
            else:
                ST2(f"\4[WCS]\1 Вам выдали \5{', '.join(weapons)}\1,"
                    f" у вас осталось \5{money}$\1").send(self.owner.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value


class MiniMap(ActiveSkill, repeat_functions):

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Setting update map type based on user settings
        self.update_map = self.update_map_default

        # Map scale modifier
        self.scale_modifier = 0.04
        if self.settings['size increase']: self.scale_modifier += 0.02
        if self.settings['size decrease']: self.scale_modifier -= 0.02

        # repeat_functions initialize
        self.repeat = Repeat(self.update_map)
        self.repeat_delay = 0.5
        if self.settings['update multiply 1']: self.repeat_delay /= 2
        if self.settings['update multiply 2']: self.repeat_delay /= 2

        self.center_position = None
        self.entity_list = []

        # Active skill initialize
        self.cd = 1
        self.delay = Delay(self.cd//2, self.cd_passed)

        # Map turn-off
        self.turn_off_length = 5
        self.turn_off_delay = None

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Вы можете создать миникарту длительностью "
            f"\5{self.turn_off_length:.1f}\1 и откатом в "
            f"\5{self.cd:.1f}\1с").send(self.owner.index)

    def bind_pressed(self) -> None:

        # Activate map, if ability not on cooldown
        if super().bind_pressed():
            self.activate_map()

    def bind_released(self) -> None:
        ...

    def calculate_orb_position(self, target: WCS_Player):
        """Calculates vector player->enemy"""
        return self.center_position + ((target.origin - self.owner.origin) * self.scale_modifier)

    def activate_map(self):

        # Is map already loaded?
        if self.center_position:

            # Turn of map first
            self.deactivate_map()

            # Rerun delay
            self.turn_off_delay.cancel()

        self.center_position = self.owner.view_coordinates
        self.center_position[2] += 20

        # Spawning center of map (not owner, view_coordinates + height)
        self.entity_list.append([effect.persistent_orb(
            origin = self.center_position,
            color=(0, 0, 255),
            scale = 0.1,
            sprite = 1,
        ), self.owner])

        # Is player skill improved with penetrate power?
        if self.settings['penetrate immune']:

            # Yes. Set penetrate Type
            penetrate = ImmuneTypes.Penetrate

        else:

            # No. Set default type
            penetrate = ImmuneTypes.Default

        # Iterating over all players and setting ball
        for player in WCS_Player.iter():

            # Detect check
            answer = immunes_check(
                player,              # Targeting victim
                penetrate,           # Map check consider to be more Default, then Ultimate actually
                'detect',            # MiniMap is detecting type
                self.detect_deflect, # After deflect call self.detect_deflected function
                # Next goes arguments, that will be passed to self.detect_deflect on deflect
                player               # Pass player, that deflected detect
            )

            # Go to the next loop, if player immune/deflect against detect
            if answer != ImmuneReactionTypes.Passed: continue

            if player.team_index == self.owner.team_index: # Player in our team?
                color = (0, 255, 0) # Setting green color
            else:
                color = (255, 0, 0) # Setting red color

            # Spawning orb
            orb_ent = effect.persistent_orb(
                origin = self.calculate_orb_position(player),
                color =  color,
                scale = 0.1,
                sprite = 1
            )

            # Spawning orb
            self.entity_list.append([orb_ent, player])

        # Starting update repeat
        self._repeat_start()

        # Delay map disable
        self.turn_off_delay = Delay(self.turn_off_length, self.deactivate_map)

    def update_map(self):
        raise NotImplementedError("__init__ should assign update_map a function")

    def update_map_default(self):
        pop_counter = 0

        for num, (orb_ent, player) in enumerate(self.entity_list.copy()):

            # Pop player from list, if killed
            if player.health <= 0:
                orb_ent.remove()
                self.entity_list.pop(num-pop_counter)
                pop_counter += 1

            # Calculating vector player->enemy
            orb_ent.teleport(origin=self.calculate_orb_position(player))

    def deactivate_map(self):

        # Map activated?
        if not self.center_position:

            # No, return
            return

        # Deleting entity's
        for entity, player in self.entity_list: entity.remove()

        # Clearing list
        self.entity_list.clear()

        # Clear center position (mark: map doesn't exist)
        self.center_position = None

        # Stop update repeat
        self._repeat_stop()

    def detect_deflect(self, user):
        """Called when map detection is deflected"""

        # Notify victim
        ST2("\4[WCS]\1 Вы защитились от навыка обнаружения игрока \5"
            f"{self.owner.name:.10}\1").send(user.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self.deactivate_map()


class Static_Mine(ActiveSkill):
    __slots__ = ('mine_dict', 'damage_amount')

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Active ability variables
        self.cd = 5
        self.delay = Delay(self.cd//2, self.cd_passed)

        # Amount of damage, that dealt by explode of mine
        self.damage_amount = 30

        # Set, that contains active mines.
        self.mine_dict: dict[str, tuple[Entity, Entity]] = dict()

        # Applying for entity output listener to listen for trigger activate
        OnEntityOutputListenerManager.register_listener(self.entity_output)

    def bind_pressed(self) -> None:
        if super().bind_pressed():

            name = f"Static_mine({randint(0,10000)})"

            # Setting mine origin
            spawn_location = self.owner.view_coordinates *0.99
            spawn_location[2] += 50

            with persistent_entity('prop_static') as mine_model:
                mine_model.model = Model('models\\props_crates\\static_crate_40.mdl')
                mine_model.origin = spawn_location
                mine_model.solid = 6
            mine_model.health = 50000

            # Creating trigger for mine
            trigger = Triggers.multiple(spawn_location - 50, spawn_location + 50)

            # Adding target_name to trigger to identify him in next function calls
            trigger.target_name = name

            # Creating list for future [Prop, Trigger] list
            self.mine_dict[name] = mine_model, trigger

            # Mine placed. Delay skill
            self.delay = Delay(self.cd, self.cd_passed)

    def bind_released(self) -> None: pass

    def entity_output(self, name: str, activator: Entity, caller: Entity, value, delay):
        if name != 'OnTrigger': return
        if caller.target_name not in self.mine_dict: return

        # Dealing with WCSP. Activator always WCSP, because:
        # Trigger works only for players =>  Dealing with
        # All players are WCS_Player-s   =>  WCS_Player
        activator: WCS_Player = WCS_Player.from_index(activator.index)

        # Is activator resisted to detect?
        resist: ImmuneReactionTypes = immunes_check(activator,
            ImmuneTypes.Default,
            'detect',
            self.explode_deflect,
            activator
        )

        if resist is ImmuneReactionTypes.Immune:
            # Notify victim
            ST2("\4[WCS]\1 Вы защитились от мины игрока \5"
                f"{self.owner.name:.10}\1. Мина не сработала").send(activator.index)

            # Break further changes
            return

        # Nothing changed, if user deflected/Immune
        if resist is not ImmuneReactionTypes.Passed: return

        # Remove trigger and model_prop entities + popping them from mine_dict
        [entity.remove() for entity in self.mine_dict.pop(caller.target_name)]

        # Dealing damage to activator
        activator.take_damage(
            damage = self.damage_amount,
            damage_type = WCS_DAMAGE_ID,
            attacker_index = self.owner.index
        )

    def explode_deflect(self, player: WCS_Player):
        # Notify victim
        ST2("\4[WCS]\1 Вы защитились от мины игрока \5"
            f"{self.owner.name:.10}\1. Мина не сработала").send(player.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        for prop, mine in self.mine_dict.values():
            mine.remove()
            prop.remove()


class Ghost_on_Knife(BaseSkill):
    """
    Giving benefits to player, that picks knife. Now applies:
    • Speed
    • Invisibility
    Also there's an option to linger property longer after switch
    """

    __slots__ = ('enabled', 'invisibility', 'speed', 'linger_length')

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings, exclude_costs=False)

        # Holds status of skill
        # False: user holds NOT knife. Skill benefits OFF
        # True: user hold knife.       Skill benefits ON
        self.enabled = None
        # Now set to None, because user can hold knife of perk start.
        if self.owner.active_weapon.weapon_name == 'weapon_knife':
            self.activate()
        else: self.enabled = False

        # Modifiers on activation
        self.invisibility = 0
        self.speed = 0
        self.linger_length = 0

        # Calculating modifiers

        # If invisibility proportion != 0
        if self.settings['speed invisibility proportion']:

            # If above 100, setting to 90
            if self.settings['speed invisibility proportion'] > 90:
                self.settings['speed invisibility proportion'] = 90

            levels_subtracted = int(self.settings['speed invisibility proportion'] * 5040)

            # Subtracting cost
            left = self.lvl - levels_subtracted

            # If level enough to full upgrade, set invis to full and assign to lvl left levels
            if left >= 0:
                self.invisibility = int(self.settings['speed invisibility proportion']*100)

                # Updating lvl with left levels
                self.lvl = left

            # Not enough
            else:
                # Calculate value
                self.invisibility = int(self.lvl/90) # 1% invisibility per lvl

                # All levels depleted. Set them to zero
                self.lvl = 0

        # No invisibility
        else: self.invisibility = 0

        # Lingering
        if self.settings['properties linger']:

            # Subtracting cost
            left = self.lvl - self.costs['properties linger']

            # If level enough to full upgrade, set invis to full and assign to lvl left levels
            if left >= 0:
                self.linger_length = 1

                # Updating lvl with left levels
                self.lvl = left

            # Not enough
            else:
                # Calculate value
                self.linger_length = (-left) / 1000

                # All levels depleted. Set them to zero
                self.lvl = 0

        # No linger
        else: self.linger_length = 0

        if self.lvl:

            self.speed += (self.lvl / 100) / 100

        # No speed
        else: self.speed = 0

        # Registering for equipment change event
        event_manager.register_for_event('item_equip', self.event_fire)

        # Notifying user
        if self.owner.data_info['skills_activate_notify']:
            # Sending first message
            ST2("\4[WCS]\1 При взятие ножа, вы получаете:").send(self.owner.index)

            # Buffs description
            if self.invisibility: ST2(f"• \5{self.invisibility:.0f}%\1 невидимости").send(self.owner.index)
            if self.speed: ST2(f"• Увеличение скорости на \5{self.speed*100:.0f}%\1").send(self.owner.index)
            if self.linger_length: ST2(f"• Эффект остаётся на \5{self.linger_length:.2f}"
                               "\1 секунд после смены оружия").send(self.owner.index)

            # Notify about something wrong, if nothing is activated
            if not any((self.invisibility, self.speed, self.linger_length)):
                ST2(F"\3Ничего\1. Проверьте настройки навыка").send(self.owner.index)

    def event_fire(self, ev):

        # Reject other players
        if ev['userid'] != self.owner.userid: return

        # Activating conditions
        elif all((ev['item'] == 'knife', self.enabled == False)):

            # Calling activate method
            self.activate()

        # Deactivating conditions
        elif all((ev['item'] != 'knife', self.enabled == True)):

            # We should delay deactivate, if linger is set
            return Delay(self.linger_length, self.deactivate) if self.linger_length else self.deactivate()

    def activate(self):

        # Marking activation
        self.enabled = True

        # Adding speed
        self.owner.speed += self.speed

        # Adding invisibility
        self.owner.invisibility = round(self.invisibility*2.55)

    def deactivate(self):

        # Marking deactivation
        self.enabled = False

        # Removing speed
        self.owner.speed -= self.speed

        # Removing invisibility
        self.owner.invisibility = 0

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()

        # Deactivating, if activated
        if self.enabled: self.deactivate()

        # Unregistering from item switch event
        event_manager.unregister_for_event('item_equip', self.event_fire)


class Light_Aura_Regenerate(BaseSkill, repeat_functions):
    __slots__ = ('interval', 'hp', 'radius')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # check for affinity
        if not affinity_check(self.owner, AffinityTypes.LIGHT):
            # User affinity is different from current skill

            # Notify owner
            if self.owner.data_info['affinity_conflict_notify']:
                ST2("\4[WCS]\1 Возник конфликт сущности!").send(self.owner.index)

            # Disables close function
            self.close = super().close

            # Disables future activation
            return

        # Checks for level for proper interval/radius/hp scaling

        # 2010 -> infinity
        # Interval: 7
        # Hp:       Continues previous scaling
        # Radius:   2000
        if self.lvl >= 2010:
            self.interval = 7
            self.hp = 91 + self.lvl // 100
            self.radius = 2000

        # 901 -> 2010
        # Interval: Scaling from 17 to 10 with step 1
        # Hp:       Scaling from 100 to infinite with step 100
        # Radius:   Continues previous scaling
        elif self.lvl > 900:
            self.interval = 7
            self.hp = 91 + self.lvl // 100
            self.radius = self.lvl - 10

        # 11 -> 900
        # Interval: 7
        # Hp:       Scaling from 10 to 100 with step 10
        # Radius:   Continue scaling
        elif self.lvl > 10:
            self.interval = 7
            self.hp = 10 + self.lvl // 10
            self.radius = self.lvl - 10

        # 0 -> 10
        # Interval: Scaling from 17 to 10 with step 1
        # Hp:       5
        # Radius:   0
        else:
            self.interval = 17 - self.lvl
            self.hp = 10
            self.radius = 0

        self.repeat = Repeat(self.heal)
        self.repeat_delay = self.interval
        self._repeat_start()

        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            ST2("\4[WCS]\1 Аура регенерации "
                f"\5{self.hp}\1хп/\5{self.interval}\1с радиусом "
                f"\5{self.radius:.0f}\1").send(self.owner.index)

    def heal(self) -> None:

        # Healing owner
        healed: int = self.owner.heal(self.hp)
        if self.settings['notify'] and healed > 0:
            ST2(f"\4[WCS]\1 Вы исцелились на \5{healed}\1хп "
                "(Аура регенерации)").send(self.owner.index)

        # Healing teammates
        for player in self.owner.players_around(self.radius, True):

            # Check for affinity. No heal for demons. Deal damage them!
            if player.affinity == AffinityTypes.DARK:
                ST2(f"\4[WCS]\1 Вы получили \5{1}\1 "
                    "урон из-за ауры исцеления игрока \5"
                    f"{self.owner.name}\1" ).send(player.index)
                player.take_damage(
                    damage = 1,
                    damage_type = WCS_DAMAGE_ID,
                    attacker_index = self.owner.index
                )
                continue

            # All is ok with teammate race
            healed: int = self.owner.heal(self.hp)
            ST2(f"\4[WCS]\1 Вас исцелил игрок \5{self.owner.name}\1"
                f" на \5{healed}\1хп").send(player.index)

    @BaseSkill.efficiency.setter
    def efficiency(self, value: float) -> None:
        super().efficiency = value

    def close(self) -> None:
        super().close()
        self._repeat_stop()

# class (BaseSkill):
#     __slots__ = ('', )
#     def __init__(self, userid: int, lvl: int, settings: dict) -> None:
#         super().__init__(userid, lvl, settings)
#     def close(self) -> None:
#         super().close()
#     @BaseSkill.efficiency.setter
#     def efficiency(self, value: float) -> None:
#         ...
