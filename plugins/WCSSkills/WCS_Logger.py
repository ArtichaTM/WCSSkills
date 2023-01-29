from datetime import datetime
from typing import Any

from .other_functions.constants import PATH_TO_LOG


class _wcs_logger:
    __slots__ = ('file',)
    path = PATH_TO_LOG

    def __init__(self):

        # Does the parent directory exist?
        if not self.path.parent.isdir():

            # Create the parent directory
            self.path.parent.makedirs()

        # Opening file
        self.file = open(self.path, mode='a', encoding='utf-8')

    def __call__(self, prefix: str, msg: Any, console: bool = False):

        msg = msg.replace('\n', '\n---> ')

        # Writing to file with prefix-s
        self.file.write(f"[{datetime.today().strftime('%H:%M:%S')}"
                        f" {prefix.upper().rjust(12):.12}] {msg}\n")

        # Quickly append
        self.file.flush()

        # Echo to console if needed
        if console:
            print(f'[WCSSkills {prefix.upper().rjust(7):.7}] {msg}')

    def unload_instance(self):

        # Closing logs on exit
        self.file.close()


wcs_logger = _wcs_logger()
