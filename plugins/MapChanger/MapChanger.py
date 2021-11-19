# ../MapChanger.py

# =============================================================================
# >> IMPORTS
# =============================================================================

# Python Imports
from typing import Tuple
# Time from epoch
from time import time

# Source.Python Imports
# Server command sender for spam "timeleft"
from engines.server import queue_server_command as e_s_c
# For return OutputReturn.BLOCK (console spam reduce)
from core import OutputReturn
# Console text listener
from listeners import on_server_output_listener_manager as output_listener
# HUD
from messages.base import HudMsg
# Repeat, Delay
from listeners.tick import Repeat, RepeatStatus, Delay
# Server
from engines.server import server
# Begin_new_match event
from events import event_manager
# Colors
from colors import Color
# ConVar
from cvars import ConVar
# CVar change listener
from listeners import OnConVarChanged


class _HUD_Display:
    """ Main class, that displays left time on the HUD.
    • Updates time_counter
    • Shows information for players
    """
    __slots__ = ('repeat',)

    def __init__(self):

        # Initiating repeat
        self.repeat = Repeat(self.tick, cancel_on_level_end=True)

        # Executing start function
        self.start()

        # Registering for a new match instance
        event_manager.register_for_event('begin_new_match', self.start)

    def tick(self):

        # Getting time left
        time_left = time_counter.time_left()

        # If time left for match is equals 0 seconds, then this is the last round
        if time_left == (0,0):
            HudMsg(f"Последний раунд",
                   y=-0.925, x=-0.99999, channel=807,
                   color1=Color(252, 15, 192, 0), hold_time=6).send()

        # If there's any time, game is on
        else:
            HudMsg(f"{f'{time_left[0]}'.rjust(2, '0')}:"
                   f"{f'{time_left[1]}'.rjust(2, '0')}",
                   y=-0.925, x=-0.99999, channel=807,
                   color1=Color(252, 15, 192, 0), hold_time=6).send()

    def start(self, *_):

        # Checking for server status
        # Server is loading
        if server.is_loading() or server.paused: Delay(5, self.start, cancel_on_level_end=True)

        # Server is empty
        elif server.num_clients == 0:            Delay(5, self.start, cancel_on_level_end=True)

        # Game is on
        else:

            # Is all ok with time_counter?
            if time_counter.timestamp == 0:

                # No, forcing time update
                time_counter.force_update()

            # Hud repeat started?
            if self.repeat.status != RepeatStatus.RUNNING:

                # No. Starting.
                self.repeat.start(1, execute_on_start=True)

    def unload_instance(self):

        # Stopping repeat, if present
        if self.repeat.status == RepeatStatus.RUNNING: self.repeat.stop()

        # Unregister from match begin event
        event_manager.unregister_for_event('begin_new_match', self.start)


class _Counter:
    """
    • Counts from match start
    • Returns elapsed time
    • Can be forced to update values

    Even if this class is created to use in class HUD, he can live
    separately from it
    """
    __slots__ = ('timestamp', 'mp_timelimit', 'force_update_seconds')

    def __init__(self):

        # Time from epoch to start of match
        self.timestamp = 0

        # Limit for match
        self.mp_timelimit = 0

    def force_set_time(self, minutes, seconds) -> None:
        """ Forces Counter to change start values
        :param minutes: minutes left for match
        :param seconds: seconds left for match
        :return: None, but updates values in class
        """

        # Calculating given values in seconds
        seconds_overall = minutes*60 + seconds


        # Replacin starter values
        self.timestamp = time()
        self.mp_timelimit = seconds_overall

    def time_left(self) -> Tuple[int, int]:

        # Estimated time is passed?
        if self.timestamp + self.mp_timelimit > time():

            # Getting seconds how many seconds passed
            seconds_passed = time() - self.timestamp

            # Calculating estimated seconds
            seconds_passed = abs(seconds_passed - self.mp_timelimit)

            # Transforming seconds into min:sec
            minutes = seconds_passed // 60
            seconds = seconds_passed - minutes*60

            # Returning values
            return int(minutes), int(seconds)

        else: return 0, 0

    def force_update(self):

        # Register for console output
        output_listener.register_listener(self._console_output)

        # Starting spam 'timeleft' for 'Time Remaining sec:min'
        repeat = Repeat(e_s_c, args=('timeleft',))
        repeat.start(0.1, 12, True)

        # Setting repeat variable to None, to mark it not setted
        self.force_update_seconds = None

        # Unregister console output reader with delay
        Delay(1.3, output_listener.unregister_listener, args=(self._console_output,))

    def _console_output(self, _, msg):

        # Looking only for "Time remaining: min:sec" and "* Last Round *":
        if msg[0:16] == 'Time Remaining: ':

            # Getting seconds
            seconds = int(msg[-3:len(msg)])

            # If got seconds is equal to updated, nothing must be changed
            if self.force_update_seconds == seconds: return OutputReturn.BLOCK

            # force_update_seconds is not set, setting then
            elif self.force_update_seconds is None:
                self.force_update_seconds = seconds
                return OutputReturn.BLOCK

            # How many minutes character in there
            x = 1

            # Starter position of iterating
            counter = -5

            # Minutes string
            minutes = ''

            # Iterating in 'Time Remaining min:sec'
            # from ':' to ' ' (backwards)
            while str(x).isdigit():

                # Saving digit in minutes
                minutes += msg[counter]

                # Moves position
                counter -= 1

                # Setting new character
                x = msg[counter]

            # Reversing string and converting it in integer
            minutes = int(minutes[::-1])

            # Forcing new time
            self.force_set_time(minutes, seconds)

            # Setting force_update_seconds to current second
            # to deny other script continuous
            self.force_update_seconds = seconds

        elif msg == '* Last Round *':

            # This is the last round. Forcing time with argument (0,0)
            self.force_set_time(0, 0)

        # Not our conditions. Pass
        else: return

        # Out condition completed, block command to make less spam
        return OutputReturn.BLOCK

# Singletons
time_counter = _Counter()
HUD = _HUD_Display()

@OnConVarChanged
def convar_tracker(convar, old_value):
    """ Updates values in counter after time_limit change """
    if convar.name == 'mp_timelimit':
        time_counter.force_update()

# Source.Python functions
def load(): pass
def unload(): HUD.unload_instance()