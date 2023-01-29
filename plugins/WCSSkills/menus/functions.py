# ../WCSSkills/admin/functions.py
# =============================================================================
# >> Imports
# =============================================================================
# Python Imports
from typing import Iterable, Union

# Source.Python Imports
from commands import CommandReturn
from commands.say import register_say_filter, unregister_say_filter
# Messaging
from messages.base import SayText2 as ST2

# Mod Imports
# Constants
from ..other_functions.constants import WCS_FOLDER
from ..other_functions.constants import VOLUME_MENU
# WCS_Player
from ..wcs.WCSP.wcsplayer import WCS_Player


class RMSound:
    """Namespace created to call for radio menu sounds"""

    @staticmethod
    def back(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/back.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def next(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/next.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def final(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/final.mp3', attenuation=1.6, volume=VOLUME_MENU)

    @staticmethod
    def next_menu(target):
        target.emit_sound(f'{WCS_FOLDER}/menus/continue.mp3', attenuation=1.6, volume=VOLUME_MENU)


class KeyboardTyping:
    __slots__ = ('target',
                 'previous_menu', 'previous_menu_args',
                 'success_function', 'success_function_args')

    def __init__(self,
                 target: WCS_Player,
                 previous_menu: callable,
                 success_function: callable,
                 previous_menu_args: Iterable,
                 success_function_args: Iterable):
        """
        :param target: WCS_Player, who requested typing from chat
        :param previous_menu: callable, that will be called on successful
            end of typing mechanisms
        :param success_function: function, that will be called after minimal validations.
            Should return str for unsuccessful validation (string contatins reason), and
            everything other for successful ending
        :param previous_menu_args: iterable, which elements will be passed to
            previous_menu function
        :param success_function_args: iterable, which elements will be passed to
            success_function function
        """

        # Setting variables
        self.target = target
        self.previous_menu = previous_menu
        self.success_function = success_function
        self.previous_menu_args = previous_menu_args
        self.success_function_args = success_function_args

        # Setting temp to target
        target.enter_temp = self.success_function.__qualname__

        # Registering current class to chat filters
        register_say_filter(self)

    def __call__(self, command, index, _):

        # Getting starter info
        player = WCS_Player.from_index(index)

        # If enter_temp is None, player is not using kb functions
        if player.enter_temp is None:

            # Then pass him
            return CommandReturn.CONTINUE

        # He's using kb, but not this function
        elif player.enter_temp != self.success_function.__qualname__:

            # Then pass him, to allow other filters work
            return CommandReturn.CONTINUE

        # This is our user

        # Getting his command
        entered = command.command_string

        # Requested stop
        if entered[:4].lower() == 'stop':

            # Unregister filter
            unregister_say_filter(self)

            # Sending previous menu
            self.previous_menu(*self.previous_menu_args)

            # Clearing player temp
            player.enter_temp = None

            # Blocking command
            return CommandReturn.BLOCK

        # Everything is OK. Call success function
        output: Union[str, None] = self.success_function(player, entered, *self.success_function_args)

        # If returned str, we should send this message to owner
        # If return is not str, we are good. Unregister filter
        if isinstance(output, str):
            ST2('\2[SYS]\1 ' + output).send(self.target.index)
            return CommandReturn.BLOCK

        # Everything good. Closing class
        else:

            # Clearing player temp
            self.target.enter_temp = None

            # Unregistering from chat filter
            unregister_say_filter(self)

            # Sending previous menu
            self.previous_menu(*self.previous_menu_args)
