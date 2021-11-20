from datetime import datetime
from typing import Any

from WCSSkills.other_functions.constants import PATH_TO_LOG
from paths import LOG_PATH


class WCS_Logger:
    __slots__ = ('file',)

    def __init__(self, path):
        log_path = LOG_PATH / path

        # Does the parent directory exist?
        if not log_path.parent.isdir():

            # Create the parent directory
            log_path.parent.makedirs()

        # Opening file
        self.file = open(log_path, mode='a', encoding='utf-8')

    def unload_instance(self):

        # Closing logs on exit
        self.file.close()

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


wcs_logger = WCS_Logger(PATH_TO_LOG)