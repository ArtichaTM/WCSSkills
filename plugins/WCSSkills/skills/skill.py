# ../WCS/wcs/skills.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
# Math
from random import randint
from math import sqrt

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

# Plugin Imports
# Functions
from .functions import *
# WCS_Player
# from WCSSkills.wcs.wcsplayer import WCS_Players
from WCSSkills.wcs.wcsplayer import WCS_Player
# Effects
from WCSSkills.other_functions.wcs_effects import effect
# Skills information
from WCSSkills.db.wcs import Skills_info
# Useful functions
from WCSSkills.other_functions.functions import *
# Constants
from WCSSkills.other_functions.constants import WCS_DAMAGE_ID
from WCSSkills.other_functions.constants import WCS_FOLDER
from WCSSkills.other_functions.constants import DamageTypes
# Enumeratings
from WCSSkills.other_functions.constants import ImmuneTypes
from WCSSkills.other_functions.constants import ImmuneReactionTypes

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = (

# Skills
'Heal_per_step', # Heals every step
'Start_add_speed', # Adds speed after start of round
'Start_set_gravity', # Adds gravity after start of round
'Long_jump', # Boosts jump
'Regenerate', # Default regeneration with intervals
'Health', # Adds health after start of round
'Slow_fall', # Slowing fall
'Nearly_Aim', # Helps to aim, when user fires in body/legs/...
'Trigger', # Fires when player comes into sight
'Start_add_max_hp', # Adds max health after start of round
'Teleport', # Teleports player
'Aim', # Full aim from every angle, but with lower chances
'WalkOnAir', # Allow player to walk on air and fire without distortion
'Poison', # Poisons player with damage every second
'Ammo_gain_on_hit', # Adds ammo on successful hit
'Additional_percent_dmg', # Deals addition damage as magic
'Auto_BunnyHop', # Allows players to auto jump with some limit
'Paralyze', # Paralyze player on hit (with cd)
'Smoke_on_wall_hit', # Instantly smoke when touch something
'Damage_delay_defend', # Delays all physical damage
'Toss', # Toss player in the air (with constants cd)
'Mirror_paralyze', # Paralyze when being hit
'Vampire_damage_percent', # Gives owner hp as percent of damage dealt
'Drop_weapon_chance', # Drops enemy weapon with such chance
'Screen_rotate_attack', # Rotates enemy screen with a chance
)

# =============================================================================
# >> Skills
# =============================================================================

class BaseSkill:
    __slots__ = ('owner', 'lvl', 'settings')

    def __init__(self, userid: int, lvl: int, settings: dict):
        self.owner = WCS_Player.from_userid(userid)
        max_lvl = Skills_info.get_max_lvl(f"skill.{type(self).__name__}")

        # Getting settings
        self.settings = settings

        # Loading price for settings
        costs = Skills_info.get_settings_cost(f"skill.{type(self).__name__}")

        # Subtract lvl for each setting
        for setting, value in self.settings.items():

            # If setting active
            if value is True:

                # Subtracting it's cost
                lvl -= costs[setting]

        # # Lvl limits check

        # Lvl equals -1 -> no limit to lvl
        if max_lvl == -1:

            self.lvl = lvl

        # Lvl above maximum -> Change lvl to max
        elif lvl > max_lvl:
            self.lvl = max_lvl

        # Lvl below minimum -> Change lvl to 0
        elif lvl < 0:

            self.lvl = 0

        # All is ok, set lvl as in arguments
        else:

            self.lvl = lvl

    def __repr__(self):
        return (f"{self.__class__.__name__}(lvl={self.lvl}, "
               f"settings={self.settings}, owner = {self.owner.__repr__()})")

    def close(self) -> None:
        pass

class ActiveSkill(BaseSkill):
    """
    Inherit this class, if u need to create ultimate/ability
    """
    __slots__ = ('delay',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings),

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
    __slots__ = ('infect_dict',)

    def __init__(self, lvl: int, userid: int, settings: dict):
        super().__init__(userid, lvl, settings)

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
    __slots__ = ('cd', 'cd_length')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # length of cd
        self.cd_length = 0

        # Delay
        self.cd = Delay(0, self.cd_passed)

    def cd_passed(self):
        pass

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
        self.owner.heal(self.lvl, ignore = True)

        if self.owner.data_info['skills_activate_notify']:
            # Notifying player
            ST2(f"\4[WCS]\1 Вы получили \5{self.lvl}\1 к хп").send(self.owner.index)

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

    def close(self) -> None:
        super().close()

        # Removing added speed
        self.owner.speed -= self.speed/100

class Regenerate(BaseSkill, repeat_functions):
    __slots__ = ('interval', 'hp')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        if self.lvl > 10:
            self.interval = 7
            self.hp = 5 + self.lvl // 100
        else:
            self.interval = 17 - self.lvl
            self.hp = 5

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

    def close(self) -> None:
        super().close()
        if self.lvl == 1000:
            self.owner.move_type = MoveType.WALK
        else:

            # Removing added gravity
            self.owner.gravity = 1

class Long_jump(BaseSkill):
    """
    Skill that speed ups player on jump

    Maximum lvl: 999
    Maximum lvl skill: Power of jump multiplied 100 times
    """
    __slots__ = ('power',)

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        # Saving basic information into instance
        if self.lvl == 0:
            self.power = 1
        else:
            self.power = self.lvl / 100

        if self.owner.data_info['skills_activate_notify']:
            # Notifies player about perk activation
            if self.power == int(self.power):
                ST2("\4[WCS]\1 Длина вашего прыжка увеличена в "
                f"\5{int(self.power)}\1 раз").send(self.owner.index)
            else:
                ST2("\4[WCS]\1 Длина вашего прыжка увеличена в "
                f"\5{self.power}\1 раз").send(self.owner.index)

        # Registration for player jump
        event_manager.register_for_event('player_jump', self.jump)

    def jump(self, ev) -> None:
        # Check if event is fired by owner of this skill
        if ev['userid'] == self.owner.userid:
            if self.owner.get_property_bool('m_bHasWalkMovedSinceLastJump'
                '') or self.settings['allow_bhop']:
                print(self.owner.get_property_bool('m_bHasWalkMovedSinceLastJump'))
                Delay(0, self.speed_up)

    def speed_up(self) -> None:
        vel = self.owner.velocity
        vel[0] = vel[0] * self.power
        vel[1] = vel[1] * self.power
        self.owner.teleport(velocity = vel)

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

        # Check for conflict with other perks


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

class Start_add_max_hp(BaseSkill):

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)

        self.owner.max_health += self.lvl//2

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2("\4[WCS]\1 Ваше максимальное здоровье увеличено"
            f" на \4{self.lvl//2}\1").send(self.owner.index)

class Teleport(ActiveSkill):
    __slots__ = ('position', 'origin', 'cd', 'allowed_distance', 'is_pressed')

    def __init__(self, userid: int, lvl: int, settings: dict):
        super().__init__(userid, lvl, settings)
        self.position = None
        self.origin = None
        # self.cd = 30 - (self.lvl/100)
        self.cd = 2
        self.allowed_distance = 100 + lvl
        self.delay = Delay(self.cd, self.cd_passed)
        self.is_pressed = False

        # Notifying player
        if self.owner.data_info['skills_activate_notify']:
            ST2(f"\4[WCS]\1 Телепорт радиусом "
            f"\5{self.allowed_distance}\1 юнитов активирован").send(self.owner.index)

    def bind_pressed(self) -> None:
        self.position = self.owner.view_coordinates
        self.position[2] += 6
        self.is_pressed = True

    def bind_released(self) -> None:
        self.is_pressed = False
        if super().bind_released():
            distance = self.owner.origin.get_distance(self.owner.view_coordinates)
            self.origin = self.owner.origin
            if distance > self.allowed_distance:
                difference = self.origin - self.position
                coefficient = self.allowed_distance / distance
                for dimension in range(0,3):
                    self.position[dimension] = self.origin[dimension] - difference[dimension]*coefficient

            self.owner.teleport(self.position)
            self.position = None
            if self.owner.is_in_solid():
                self.owner.teleport(self.origin)
                ST2(f"\4[WCS]\1 \7Неверная позиция!\1").send(self.owner.index)
                self.delay = Delay(self.cd/10, self.cd_passed)
                return
            self.owner.emit_sound(f'{WCS_FOLDER}/skills/Teleport/success.mp3',
                                  attenuation = 0.8)
            self.delay = Delay(self.cd//2, self.cd_passed)

    def cd_passed(self) -> None:
        ST2(f"\4[WCS]\1 Телепорт \5готов\1").send(self.owner.index)
        if self.is_pressed is True and self.settings['after_cd_instantly']:
            self.bind_released()

    def close(self) -> None:
        if self.delay.running is True:
            self.delay.cancel()

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
                f"\5{'вкл' if self.back_to_aim == True else 'выкл'}\1").send(self.owner.index)

        pre_event_manager.register_for_event('weapon_fire', self.fire)

    def fire(self, ev) -> None:
        # Canceling if activated not by owner
        if ev['userid'] != self.owner.userid:
            return

        # Aborting, if chance not worked
        if not chance(self.lvl, 1500):
            return

        # Looking for player
        target = open_players(player=self.owner,
                              form = ImmuneTypes.Default,
                              only_one = True)

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

        self.owner.emit_sound(f'{WCS_FOLDER}/skills/WalkOnAir/'
                              f'success.mp3', Atenuation=0.8)

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

        try:
            attacker = WCS_Player.from_userid(ev['attacker'])
            victim = WCS_Player.from_userid(ev['userid'])
        except KeyError: return

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

        result = Throw_player_upwards(
            owner = self.owner,
            victim = victim,
            power = self.power,
            form = ImmuneTypes.Default
            )

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
            ST2(f"\4[WCS]\1 Вы исцеляете \5{self.vampire_percent*100:.1f}\1%"
                     f" здоровья от урона по врагу").send(self.owner.index)

    def player_hurt(self, ev):

        # Checking, if attack did by owner
        if ev['attacker'] != self.owner.userid:
            return

        # Calculating amount to heal
        amount_to_heal = ev['dmg_health'] * self.vampire_percent

        # Healing, and stores healed hp
        healed = self.owner.heal(amount_to_heal)

        # Notifying owner
        if self.settings['hit notify']:
            ST2(f"\4[WCS]\1 Вы исцелились на \5{healed:.1f}"
                     '\1').send(self.owner.index)

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
                     f"{self.chance:.1f}").send(self.owner.index)

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

    def close(self) -> None:
        super().close()

        # Unregister from hit
        event_manager.unregister_for_event('player_hurt', self.player_hurt)

class Screen_rotate_attack(DelaySkill):

    __slots__ = ('distortion', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        self.distortion = self.lvl / 60

        self.cd_length = 2

        # Register for hit
        event_manager.register_for_event('player_hurt', self.player_hurt)

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

    def close(self) -> None:
        super().close()

        # Unregister from hit
        event_manager.unregister_for_event('player_hurt', self.player_hurt)


class HE_Bloodhound(BaseSkill):
    # TODO: Apply detonate on next offsets fix

    __slots__ = ('power', )

    def __init__(self, userid: int, lvl: int, settings: dict) -> None:
        super().__init__(userid, lvl, settings)

        # Calculating velocity multiplier
        self.power = sqrt(self.lvl)

        # Registering for bounce event
        event_manager.register_for_event('grenade_bounce', self.check)

    def check(self, ev):

        # Delay to make grenade move from wall
        # This made for make rays didn't hit wall, that
        # grenade bouncing from
        Delay(0.1, self._check)

    def _check(self):
        for entity in EntityIter(class_names=('hegrenade_projectile',)):

            # Getting thrower index
            thrower_index = entity.get_property_short('m_hThrower')

            # Checking if it matches owner index
            if thrower_index != self.owner.index: continue

            # Looking for players
            victim = open_players(entity, ImmuneTypes.Penetrate, True, False)

            # Getting victim
            if len(victim) == 0: return
            else: victim = victim[0]

            # Applying velocity to this player
            velocity = victim.eye_location - entity.origin
            velocity *= self.power

            if velocity.length < 150:

                # Detonate
                entity.set_property_int('m_nNextThinkTick', server.tick+1)

                # Abort function
                return


            entity.teleport(velocity=velocity)

            # Adding -1 to ThinkTick, to delay his detonate
            entity.set_property_int('m_nNextThinkTick', -1)

    def close(self) -> None:
        super().close()

        # Unregistering from bounce event
        event_manager.unregister_for_event('grenade_bounce', self.check)

# class
#
#     __slots__ = ('', )
#
#     def __init__(self, userid: int, lvl: int, settings: dict) -> None:
#         super().__init__(userid, lvl, settings)