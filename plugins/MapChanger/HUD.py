# ../HUD.py

# =============================================================================
# >> IMPORTS
# =============================================================================

# Source.Python Imports
# HUD
from messages.base import HudMsg
# Repeat
from listeners.tick import Repeat, RepeatStatus, Delay
# events
from events import event_manager

# Plugin Imports
from .counter import time_counter

# Map start event
from listeners import on_server_output_listener_manager

from colors import Color

from engines.server import server
from engines.server import execute_server_command as e_s_c
from core import OutputReturn


def time_left_spam():
    e_s_c('timeleft')

def time_left_spam_stop(repeat):
    repeat.stop()





class _HUD_Display:
    __slots__ = ('repeat','deactivate_delay')

    def __init__(self, force=False):

        self.repeat = Repeat(self.tick, cancel_on_level_end=True)

        if server.is_active():

            # Register for console output
            on_server_output_listener_manager.register_listener(self.console_output)

            if self.repeat.status != RepeatStatus.RUNNING:
                self.repeat.start(1)

        repeat = Repeat(lambda : e_s_c('timeleft'))
        repeat.start(0, limit = 300)
        Delay(1.5, on_server_output_listener_manager.unregister_listener,
              args=(self.console_output,))

    def tick(self):

        time_left = time_counter.time_left()
        if time_left == (0,0):
            HudMsg(f"Последний раунд",
                   y=-0.92, x=-0.99999, channel=807,
                   color1=Color(252, 15, 192, 0), hold_time=6).send()
        else:
            HudMsg(f"{f'{time_left[0]}'.rjust(2, '0')}:"
                   f"{f'{time_left[1]}'.rjust(2, '0')}",
                   y=-0.92, x=-0.99999, channel=807,
                   color1=Color(252, 15, 192, 0), hold_time=6).send()

    def console_output(self, _, msg):

        if msg[0:16] == 'Time Remaining: ':
            seconds = int(msg[-3:len(msg)])

            x = 1
            counter = -5
            minutes = ''

            while str(x).isdigit():
                minutes += msg[counter]
                counter -= 1
                x = msg[counter]

            minutes = [*minutes]
            minutes.reverse()
            minutes = int(''.join(minutes))

            time_counter.force_set_time(minutes, seconds)


        elif msg == '* Last Round *':

            time_counter.force_set_time(0, 0)

        else:
            return

        return OutputReturn.BLOCK

    def map_start(self, _):
        time_counter.map_start(None)
        self.repeat.start(5)

    def unload_instance(self):
        if self.repeat.status == RepeatStatus.RUNNING:
            self.repeat.stop()

HUD = _HUD_Display()