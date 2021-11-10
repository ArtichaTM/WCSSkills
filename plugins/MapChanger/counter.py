# ../counter.py

# =============================================================================
# >> IMPORTS
# =============================================================================

# Python Imports
from typing import Tuple
# Time
from time import time

# =============================================================================
# >> Classes
# =============================================================================

__all__ = ('time_counter',)

# =============================================================================
# >> Classes
# =============================================================================

class _Counter:
    __slots__ = ('hud', 'timestamp', 'mp_timelimit')

    def __init__(self):

        # Starter values
        self.timestamp = 0
        self.mp_timelimit = 0

    def force_set_time(self, minutes, seconds):
        seconds_overall = minutes*60 + seconds

        self.timestamp = time()
        self.mp_timelimit = seconds_overall

    def time_left(self) -> Tuple[int, int]:
        if self.timestamp + self.mp_timelimit > time():
            seconds_passed = time() - self.timestamp
            seconds_passed = abs(seconds_passed - self.mp_timelimit)

            minutes = seconds_passed // 60
            seconds = seconds_passed - minutes*60

            return int(minutes), int(seconds)
        else: return 0, 0

time_counter = _Counter()