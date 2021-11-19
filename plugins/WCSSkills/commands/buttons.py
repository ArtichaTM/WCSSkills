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

# Plugin imports
# Info about skills
from WCSSkills.db.wcs import Skills_info

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

    __slots__ = ('owner', 'hud_update_repeat', 'HUD_limit', 'active_buttons',
                 'buttons', 'button_names', 'skills', 'skills_names'
                 )

    def __init__(self, player):

        # Player, that holds this instance
        self.owner = player

        # List of buttons, that player has
        self.buttons = []
        # List of buttons names
        self.button_names = []
        # Variable to check if buttons can be used
        self.active_buttons = 0
        # Initiating message

        # List of skills (with cd), that player has
        self.skills = []
        # List of skills names
        self.skills_names = []

        # Initiating repeat function, that update HUD
        self.hud_update_repeat = Repeat(self.hud_update)

    def round_start(self):
        """
        Function called when all skills a loaded by WCS_Player
        • Registering for commands
        • Notify player
        • Creating message for skills with cooldown
        """

        # If player has 0 active abilities and 0 delay skills - return
        if not self.buttons and not self.skills:
            self.active_buttons = 0
            return

        elif len(self.buttons) > 2:
            SayText2(f"\4[WCS]\1 Введено более 2 активных способностей,"
                     ).send(self.owner.index)

        if len(self.buttons) >= 1:

            # Getting skill name
            name = Skills_info.get_name(self.buttons[0].name)

            # Starting hud update. Here u can change how fast
            self.active_buttons = 1

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
            name = Skills_info.get_name(self.buttons[1].name)

            # Registering for commands
            client_command_manager.register_commands('+ability', self.abi_pressed)
            client_command_manager.register_commands('-ability', self.abi_released)

            # Marking amount of active skills
            self.active_buttons = 2

            # Player notify
            if self.owner.data_info['ultimates_activate_notify']:
                SayText2("\4[WCS]\1 Активирован абилити "
                f"\5{name}\1").send(self.owner.index)

            # Adding skill name to list
            if self.owner.data_info['active_skill_name_length_limit']:
                self.button_names.append(f"{name:.10}")
            else: self.button_names.append(name)

        if self.skills:

            # Calculating limit
            limit = 5 - self.active_buttons

            # Limiting self.skills
            self.skills = self.skills[:limit]

            for skill in self.skills:

                # Setting skill name
                self.skills_names.append(Skills_info.get_name(skill.name))


        # for num, skill in enumerate(self.skills):
        #     if num > 1: break
        #

        # Starting HUD repeat
        self.hud_update_repeat.start(1,execute_on_start=True)

    def hud_update(self):
        # User disabled ultimate display?
        if not self.owner.data_info['ultimate_hud']:

            # Yes, pass ultimate
            pass

        # Is here any active skills?
        elif not self.buttons: pass

        # Checking for cooldown
        elif self.buttons[0].delay.running is True:

            # Calculating values for color
            remaining = self.buttons[0].delay.time_remaining
            Col = self.color_calculate(self.buttons[0].delay)

            # Displaying ult in HUD
            HudMsg(f"{self.button_names[0]}: {remaining:.1f}".rjust(10),
                y=-0.13,  channel=1210, color1=Col, hold_time=1.2).send(self.owner.index)

        # CD is passed
        else:

            # Constant color
            Col = Color(0,255,0,255)

            # Displaying ult in HUD
            HudMsg(f"{self.button_names[0]}: готов",
                y=-0.13, channel=1210, color1=Col, hold_time=1.2).send(self.owner.index)

        # Is there's an ability, and ability display is ON?
        if not (len(self.buttons) == 2 and self.owner.data_info['ability_hud']): pass

        # Checking for cooldown
        elif self.buttons[1].delay.running is True:

            # Calculating values for color
            remaining = self.buttons[1].delay.time_remaining
            Col = self.color_calculate(self.buttons[1].delay)

            # Displaying abi in HUD
            HudMsg(f"{self.button_names[1]}: {remaining:.1f}",
                y=-0.1, channel=1211, color1=Col, hold_time=1.2
                   ).send(self.owner.index)

        # Cooldown is passed
        else:

            # Displaying abi in HUD
            HudMsg(f"{self.button_names[1]}: готов", y=-0.1,
                channel=1211, color1=Color(0,255,0,255), hold_time=1.2
                   ).send(self.owner.index)

        for num, skill in enumerate(self.skills):

            position = self.active_buttons + num

            y_pos = -0.1 - 0.03*position
            channel = 1212+num

            # Checking for cooldown
            if skill.cd.running is True:

                # Calculating values for color
                remaining = skill.cd.time_remaining
                Col = self.color_calculate(skill.cd)

                # Displaying abi in HUD
                HudMsg(f"{self.skills_names[num]}: {remaining:.1f}",
                       y=y_pos, channel=channel, color1=Col, hold_time=1.2
                       ).send(self.owner.index)

            # Cooldown is passed
            else:

                # Displaying abi in HUD
                HudMsg(f"{self.skills_names[num]}: готов", y=y_pos,
                       channel=channel, color1=Color(0, 255, 0, 255), hold_time=1.2
                       ).send(self.owner.index)



    @staticmethod
    def color_calculate(delay) -> Color:
        elapsed = delay.time_elapsed
        total = delay.delay
        try: xz = elapsed/total
        except ZeroDivisionError: return
        value = int(255*xz)
        return Color(255-value,value,0,255)

    def ult_pressed(self, _, index):
        if index == self.owner.index:
            self.buttons[0].bind_pressed()
            return CommandReturn.BLOCK

    def ult_released(self, _, index):
        if index == self.owner.index:
            self.buttons[0].bind_released()
            return CommandReturn.BLOCK

    def abi_pressed(self, _, index):
        if index == self.owner.index:
            self.buttons[1].bind_pressed()

    def abi_released(self, _, index):
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
                    self.button_names[num] = Skills_info.get_name(button.name)

    def unload(self):
        if self.active_buttons != 0:
            if self.active_buttons >= 1:
                client_command_manager.unregister_commands('+ultimate', self.ult_pressed)
                client_command_manager.unregister_commands('-ultimate', self.ult_released)
            if self.active_buttons >= 2:
                client_command_manager.unregister_commands('+ability', self.abi_pressed)
                client_command_manager.unregister_commands('-ability', self.abi_released)
            self.hud_update_repeat.stop()
            self.buttons.clear()
            self.button_names.clear()
            self.active_buttons = 0

        self.skills.clear()

    def close(self):
        self.unload()