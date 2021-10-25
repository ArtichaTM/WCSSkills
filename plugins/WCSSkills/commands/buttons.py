# ../WCSSkills/commands/buttons.py
"""
This file holds "Buttons" class that realizes
ultimate/ability use
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
    __slots__ = ('owner', 'buttons', 'active_skills',
                 'hud1', 'hud2', 'hud_update_repeat')

    def __init__(self, player):

        # Player, that holds this instance
        self.owner = player

        # List of buttons, that player has
        self.buttons = []

        # Variable to check if buttons can be used
        self.active_skills = 0

        # Initiating message
        self.hud1 = HudMsg(" ", y=-0.1, channel=11)
        self.hud2 = HudMsg(" ", y=-0.13, channel=12)

        # Initiating repeat function, that update HUD
        self.hud_update_repeat = Repeat(self.hud_update)

    def round_start(self):

        if len(self.buttons) == 0:
            # If player has 0 active abilities, break
            self.active_skills = 0
            return
        elif len(self.buttons) > 2:
            SayText2(f"Введено более 2 активных способностей").send(self.owner.index)
            return
        if 1 <= len(self.buttons) <= 2:
            # Starting hud update. Here u can change how fast
            self.hud_update_repeat.start(0.5,execute_on_start=True)
            self.active_skills = 1

            name = Skills_info.get_name(type(self.buttons[0]).__name__)
            client_command_manager.register_commands(
                ('+ultimate',
                '-ultimate'),
                self.call)

            if self.owner.data_info['ultimates_activate_notify']:
                SayText2("\4[WCS]\1 Активирован ультимейт "
                f"\5{name}\1").send(self.owner.index)

        if len(self.buttons) == 2:
            name = Skills_info.get_name(type(self.buttons[1]).__name__)
            client_command_manager.register_commands(
                (
                '+ability',
                '-ability'
                ), self.call)
            self.active_skills = 2
            if self.owner.data_info['ultimates_activate_notify']:
                SayText2("\4[WCS]\1 Активирован абилити "
                f"\5{name}\1").send(self.owner.index)
            return

    def hud_update(self):
        if not self.owner.data_info['ultimate_hud']:
            pass
        elif self.buttons[0].delay.running is True:
            remaining = self.buttons[0].delay.time_remaining
            elapsed = self.buttons[0].delay.time_elapsed
            total = self.buttons[0].delay.delay
            try:
                xz = elapsed/total
            except ZeroDivisionError:
                return
            value = int(255*xz)
            Col = Color(255-value,value,0,255)
            self.hud1 = HudMsg(f"Ультмейт: {remaining:.1f}", y=-0.1,
            channel=11, color1=Col, hold_time=1.2).send(self.owner.index)
        else:
            Col = Color(0,255,0,255)
            self.hud1 = HudMsg("Ультимейт: готов", y=-0.1,
            channel=11, color1=Col, hold_time=1.2).send(self.owner.index)
        if not self.owner.data_info['ability_hud']:
            return
        elif len(self.buttons) == 2:
            if self.buttons[1].delay.running is True:
                self.hud2 = HudMsg("Абилити: "
                f"{self.buttons[1].delay.time_remaining:.1f}",
                y=-0.13, channel=12, hold_time=1.2).send(self.owner.index)
            else:
                self.hud2 = HudMsg("Абилити: готов", y=-0.13,
                channel=12, hold_time=1.2).send(self.owner.index)

    def call(self, command, index):
        if index == self.owner.index:
            command = command.command_string
            if command[1] == 'u': command = command[0:9]
            if command[1] == 'a': command = command[0:8]

            if self.active_skills == 1:
                if command == '+ultimate':
                    self.buttons[0].bind_pressed()
                elif command == '-ultimate':
                    self.buttons[0].bind_released()
                return CommandReturn.BLOCK
            if self.active_skills == 2:
                if command == '+ultimate':
                    self.buttons[0].bind_pressed()
                elif command == '-ultimate':
                    self.buttons[0].bind_released()
                elif command == '+ability':
                    self.buttons[1].bind_pressed()
                elif command == '-ability':
                    self.buttons[1].bind_released()
                return CommandReturn.BLOCK

    def add_new_button(self, skill):
        self.buttons.append(skill)

    def _unload(self):
        if self.active_skills != 0:
            if self.active_skills >= 1:
                client_command_manager.unregister_commands(
                    ('+ultimate',
                     '-ultimate'), self.call)
            if self.active_skills >= 2:
                client_command_manager.unregister_commands(
                    ('+ability',
                     '-ability'), self.call)
            self.hud_update_repeat.stop()
            self.buttons.clear()
            self.active_skills = 0

    def close(self):
        self._unload()