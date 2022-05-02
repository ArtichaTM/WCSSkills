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
from listeners.tick import Repeat, Delay
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
                 'buttons', 'button_names', 'skills', 'skills_names')

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
        Function called when all skills loaded by WCS_Player
        • Registering for commands
        • Notify player
        • Creating message for skills with cooldown
        """

        # If player has 0 active abilities and 0 delay skills - return
        if not self.buttons and not self.skills:
            self.active_buttons = 0
            return

        # User has been set more than 2 active abilities
        elif len(self.buttons) > 2:

            # Getting those skills
            overflow_skills = self.buttons[2:]

            # Transforming from class to name string
            overflow_skills = [Skills_info.get_name(skill.name) for skill in overflow_skills]

            # Notify user
            SayText2(f"\4[WCS]\1 Введено более 2 активных способностей,"
                ).send(self.owner.index)
            SayText2(f"\4[WCS]\1 Способности \5" + '\1, \5'.join(overflow_skills) +
                "\1не активированы").send(self.owner.index)

            # Active only first two
            self.buttons = self.buttons[:2]

        if len(self.buttons) >= 1:

            # Getting skill name
            name = Skills_info.get_name(self.buttons[0].name)

            # User have only one active skill (mb 2 - unknown)
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

        # Starting HUD repeat
        self.hud_update_repeat.start(1, execute_on_start=False)

    def hud_update(self) -> None:
        """ Updates user cooldown skills HUD
        Structure of function:
        1. Ultimate
        2. Ability
        3. Skill with cooldowns

        Implementation note: Constructed by if-elif-else, to skip next code, if previous
        statements is false. The first if checks for user settings. Maybe he turned off
        ultimate or ability display. If yes, statement will pass and meet "pass" keyword,
        that doing nothing. By this, we pass other elif/else without any performance
        usage

        Schema of if-elif-else in function:
        1. IF ultimate visibility disabled, pass 1.* statements
        1.1. ELIF there's no active skills, pass 1.* statements
        1.2. ELIF ultimate on cooldown, display cooldown info
        1.3. ELSE display ultimate readiness info
        2. IF ability visibility disabled, pass 2.* statements
        2.1. ELIF ability on cooldown, display cooldown info
        2.2. ELSE display ability readiness info
        3. Iterate over cooldown skills (3.* — iteration body)
        3.1. Calculate line position and channel of msg
        3.2.1. IF skill on cooldown, display cooldown info
        3.3.2. ELSE display skill readiness info

        """
        # User disabled ultimate display?
        if not self.owner.data_info['ultimate_hud']:

            # Yes, pass ultimate
            pass

        # Is here any active skills?
        # This needed, bcz self.buttons[...] raises exception
        elif not self.buttons: pass

        # Checking for cooldown
        elif self.buttons[0].delay.running is True:
            # On cooldown

            # Calculating values for color
            remaining = self.buttons[0].delay.time_remaining
            col = self.color_calculate(self.buttons[0].delay)

            # Displaying ult in HUD
            HudMsg(f"{self.button_names[0]}: {remaining:.1f}",
                y=-0.13,  channel=1210, color1=col, hold_time=1.2).send(self.owner.index)

        else:
        # CD is passed

            # Constant color
            col = Color(0,255,0,255)

            # Displaying ult in HUD
            HudMsg(f"{self.button_names[0]}: готов", y=-0.13,
                channel=1210, color1=col, hold_time=1.2).send(self.owner.index)

        # Is there's an ability, and ability display is ON?
        if not (len(self.buttons) == 2 and self.owner.data_info['ability_hud']):

            # No, pass ability
            pass

        # Checking for cooldown
        elif self.buttons[1].delay.running is True:
            # On cooldown

            # Calculating values for color
            remaining = self.buttons[1].delay.time_remaining
            col = self.color_calculate(self.buttons[1].delay)

            # Displaying ability status in HUD
            HudMsg(f"{self.button_names[1]}: {remaining:.1f}",
                y=-0.1, channel=1211, color1=col, hold_time=1.2
                   ).send(self.owner.index)

        else:
            # Cooldown is passed

            # Displaying abi in HUD
            HudMsg(f"{self.button_names[1]}: готов", y=-0.1,
                channel=1211, color1=Color(0,255,0,255), hold_time=1.2
                   ).send(self.owner.index)


        # Iterator for skills with cooldown (not active ones)
        for num, skill in enumerate(self.skills):

            # Calculating vertical indent based on active_buttons amount
            y_pos = -0.1 - 0.03*(self.active_buttons + num)

            # Increasing channel thus they won't overlap each other
            channel = 1212+num

            # Checking for cooldown
            if skill.cd.running is True:
                # On cooldown

                # Calculating values for color
                remaining: float = skill.cd.time_remaining
                col: Color = self.color_calculate(skill.cd)

                # Displaying skill cd in HUD
                HudMsg(f"{self.skills_names[num]}: {remaining:.1f}",
                       y=y_pos, channel=channel, color1=col, hold_time=1.2
                       ).send(self.owner.index)

            else:
                # Cooldown is passed

                # Displaying skill readiness in HUD
                HudMsg(f"{self.skills_names[num]}: готов", y=y_pos,
                       channel=channel, color1=Color(0, 255, 0, 255), hold_time=1.2
                       ).send(self.owner.index)

    @staticmethod
    def color_calculate(delay: Delay) -> Color:
        """Static method to calculate color based on delay instance"""

        # Getting time passed from timer start
        elapsed = delay.time_elapsed

        # Getting target time
        total = delay.delay

        # Getting the readiness percentage
        try: percentage = elapsed/total

        # Sometimes it rises ZeroDivisionError
        # Usually, when delay is not initialized
        except ZeroDivisionError: return

        # Calculating temp value for red and green colors
        value = int(255*percentage)

        # Returning result color
        return Color(255-value,value,0,255)

    def ult_pressed(self, _, index: int) -> CommandReturn:
        """Called when any user presses +ultimate"""
        if index != self.owner.index:
            return CommandReturn.CONTINUE
        self.buttons[0].bind_pressed()
        return CommandReturn.BLOCK

    def ult_released(self, _, index: int) -> CommandReturn:
        """Called when any user presses -ultimate"""
        if index != self.owner.index:
            return CommandReturn.CONTINUE
        self.buttons[0].bind_released()
        return CommandReturn.BLOCK

    def abi_pressed(self, _, index: int) -> CommandReturn:
        """Called when any user presses +ability"""
        if index != self.owner.index:
            return CommandReturn.CONTINUE
        self.buttons[1].bind_pressed()
        return CommandReturn.BLOCK

    def abi_released(self, _, index: int) -> CommandReturn:
        """Called when any user presses -ability"""
        if index != self.owner.index:
            return CommandReturn.CONTINUE
        self.buttons[1].bind_released()
        return CommandReturn.BLOCK

    def add_new_button(self, button) -> None:
        """ Called by active skill. Add"""
        self.buttons.append(button)

    def add_new_skill(self, skill) -> None:
        self.skills.append(skill)

    def settings_changed(self, ev) -> None:
        """Called when"""
        if ev['code'] == 'active_skill_name_length_restrict' and \
        len(self.button_names) > 0:
            if ev['value'] is True:
                self.button_names = [f"{name:.10}" for name in self.button_names]
            else:
                for num, button in enumerate(self.buttons):
                    self.button_names[num] = Skills_info.get_name(button.name)

    def unload(self) -> None:
        if self.active_buttons != 0:

            # Ultimate
            if self.active_buttons >= 1:

                # Unregister ultimate commands
                client_command_manager.unregister_commands('+ultimate', self.ult_pressed)
                client_command_manager.unregister_commands('-ultimate', self.ult_released)

            # Ability
            if self.active_buttons >= 2:

                # Unregister ability commands
                client_command_manager.unregister_commands('+ability', self.abi_pressed)
                client_command_manager.unregister_commands('-ability', self.abi_released)

            # Stop repeat for hud display
            self.hud_update_repeat.stop()

            # Clear list of active skills
            self.buttons.clear()

            # ... and their names
            self.button_names.clear()

            # Set amount active skills to zero (No active skills)
            self.active_buttons = 0

        # Clear list of skills with cooldown
        self.skills.clear()

    def close(self):
        self.unload()