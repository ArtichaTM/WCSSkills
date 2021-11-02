# ../WCSSkills/commands/buttons.py
"""
This file holds "Buttons" class that realizes
• Ultiamte/Ability
• Skills with cooldown
"""
# =============================================================================
# >> IMPORTS
# =============================================================================
# Source.Python Imports
# Commands
from commands.client import client_command_manager
from commands import CommandReturn
# SayText2
from messages.base import SayText2
# HudMsg
from messages.base import HudMsg
# Colors
from colors import Color
# Repeat
from listeners.tick import Repeat
# Events
from events import event_manager

# Plugin imports
# Info about skills
from WCSSkills.db.wcs import Skills_info
from WCSSkills.events import wcs_custom_events

# =============================================================================
# >> ALL DECLARATION
# =============================================================================
__all__ = ('Buttons',)

class Buttons:
    """
    Using:
    1. Type in skill init player.Buttons.add_new_button(self)
    2. create self.delay to mark skill delay.
    If no delay, create self.delay = Delay(0,self.cd_passed)

    When active button clicked, calling bind_pressed
    When active button released, calling bind_released
    """

    __slots__ = ('owner', 'buttons', 'skills', 'active_skills', 'hud_update_repeat',
                 'button_names',
                 'button_hud1', 'button_hud2', 'skill_hud1', 'skill_hud2')

    def __init__(self, player):

        # Player, that holds this instance
        self.owner = player

        # List of buttons, that player has
        self.buttons = []

        # List of buttons names
        self.button_names = []

        # List of skills (with cd), that player has
        self.skills = []

        # Variable to check if buttons can be used
        self.active_skills = 0

        # Initiating message
        self.button_hud1 = HudMsg(" ", y=-0.1, channel=20)
        self.button_hud2 = HudMsg(" ", y=-0.13, channel=21)
        self.skill_hud1 = HudMsg(" ", y=-0.16, channel=22)
        self.skill_hud2 = HudMsg(" ", y=-0.19, channel=23)

        # Initiating repeat function, that update HUD
        self.hud_update_repeat = Repeat(self.hud_update)

    def round_start(self):
        """
        Function called when all skills a loaded by WCS_Player
        • Registering for commands
        • Notify player
        """

        # If player has 0 active abilities - return
        if len(self.buttons) == 0:
            self.active_skills = 0
            return

        elif len(self.buttons) > 2:
            SayText2(f"\4[WCS]\1 Введено более 2 активных способностей,"
                     "отмена активных способностей").send(self.owner.index)
            return

        # Getting skill name
        name = Skills_info.get_name(type(self.buttons[0]).__name__)

        # Starting hud update. Here u can change how fast
        self.active_skills = 1

        # Registering for commands
        client_command_manager.register_commands('+ultimate', self.ult_pressed)
        client_command_manager.register_commands('-ultimate', self.ult_released)

        # Player notify
        if self.owner.data_info['ultimates_activate_notify']:
            SayText2("\4[WCS]\1 Активирован ультимейт "
            f"\5{name}\1").send(self.owner.index)

        # Adding skill name to list
        if self.owner.data_info['active_skill_name_length_limit']:
            self.button_names.append(f"{name:.10}")
        else: self.button_names.append(name)

        if len(self.buttons) == 2:

            # Getting skill name
            name = Skills_info.get_name(type(self.buttons[1]).__name__)

            # Registering for commands
            client_command_manager.register_commands('+ability', self.abi_pressed)
            client_command_manager.register_commands('-ability', self.abi_released)

            # Marking amount of active skills
            self.active_skills = 2

            # Player notify
            if self.owner.data_info['ultimates_activate_notify']:
                SayText2("\4[WCS]\1 Активирован абилити "
                f"\5{name}\1").send(self.owner.index)

            # Adding skill name to list
            if self.owner.data_info['active_skill_name_length_limit']:
                self.button_names.append(f"{name:.10}")
            else: self.button_names.append(name)

        self.hud_update_repeat.start(0.5,execute_on_start=True)

    def hud_update(self):
        # User disabled ultimate display?
        if not self.owner.data_info['ultimate_hud']:

            # Yes, pass ultimate
            pass

        # Checking for cooldown
        elif self.buttons[0].delay.running is True:

            # Calculating values for color
            remaining = self.buttons[0].delay.time_remaining
            elapsed = self.buttons[0].delay.time_elapsed
            total = self.buttons[0].delay.delay
            try: xz = elapsed/total
            except ZeroDivisionError: xz = 0
            value = int(255*xz)
            Col = Color(255-value,value,0,255)

            # Displaying ult in HUD
            self.button_hud1 = HudMsg(f"{self.button_names[0]}: {remaining:.1f}".rjust(10), y=-0.13,
                              channel=20, color1=Col, hold_time=1.2).send(self.owner.index)
        # CD is passed
        else:

            # Constant color
            Col = Color(0,255,0,255)

            # Displaying ult in HUD
            self.button_hud1 = HudMsg(f"{self.button_names[0]}: готов", y=-0.13,
                          channel=20, color1=Col, hold_time=1.2).send(self.owner.index)

        # Is there's an ability, and ability display is ON?
        if len(self.buttons) == 2 and self.owner.data_info['ability_hud']:

            # Checking for cooldown
            if self.buttons[1].delay.running is True:

                # Calculating values for color
                remaining = self.buttons[1].delay.time_remaining
                elapsed = self.buttons[1].delay.time_elapsed
                total = self.buttons[1].delay.delay
                try: xz = elapsed/total
                except ZeroDivisionError: return
                value = int(255*xz)
                Col = Color(255-value,value,0,255)

                # Displaying abi in HUD
                self.button_hud2 = HudMsg(f"{self.button_names[1]}: {remaining:.1f}",
                  y=-0.1, channel=21, color1=Col, hold_time=1.2).send(self.owner.index)

            # Cooldown is passed
            else:

                # Color for a ready active skill is constant
                Col = Color(0,255,0,255)

                # Displaying abi in HUD
                self.button_hud2 = HudMsg(f"{self.button_names[1]}: готов", y=-0.1,
                          channel=21, color1=Col, hold_time=1.2).send(self.owner.index)

    def ult_pressed(self, command, index):
        if index == self.owner.index:
            self.buttons[0].bind_pressed()
            return CommandReturn.BLOCK

    def ult_released(self, command, index):
        if index == self.owner.index:
            self.buttons[0].bind_released()
            return CommandReturn.BLOCK

    def abi_pressed(self, command, index):
        if index == self.owner.index:
            self.buttons[1].bind_pressed()

    def abi_released(self, command, index):
        if index == self.owner.index:
            self.buttons[1].bind_released()

    def add_new_button(self, button):
        self.buttons.append(button)

    def add_new_skill(self, skill):
        self.skills.append(skill)

    def settings_changed(self, ev):
        if ev['code'] == 'active_skill_name_length_restrict' and \
        len(self.button_names) > 0:
            if ev['value'] is True:
                self.button_names = [f"{name:.10}" for name in self.button_names]
            else:
                for num, button in enumerate(self.buttons):
                    self.button_names[num] = Skills_info.get_name(type(button).__name__)

    def unload(self):
        if self.active_skills != 0:
            if self.active_skills >= 1:
                client_command_manager.unregister_commands('+ultimate', self.ult_pressed)
                client_command_manager.unregister_commands('-ultimate', self.ult_released)
            if self.active_skills >= 2:
                client_command_manager.unregister_commands('+ability', self.abi_pressed)
                client_command_manager.unregister_commands('-ability', self.abi_released)
            self.hud_update_repeat.stop()
            self.buttons.clear()
            self.button_names.clear()
            self.active_skills = 0

    def close(self):
        self.unload()