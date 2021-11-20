# ../WCSSkills/admin/admin_events.py
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
from datetime import datetime

# Source.Python Imports
# Listeners
from listeners import OnClientActive
# Player
from players.entity import Player
# Mute manager
from players.voice import mute_manager

# Plugin Imports
# Punishment Types
from .constants import Punishment_types
from .constants import Punishment_reasons
# Ban DB
from WCSSkills.db.admin import DB_admin
# Logging
from ..WCS_Logger import wcs_logger


@OnClientActive
def on_client_connect(index):
    player = Player(index)
    active = DB_admin.check_for_active(player.steamid,
        player.address, include_dates=True, include_reason=True)

    # Iterating over every punishment
    for punishment in active:

        if punishment[0] == Punishment_types.BAN.value[0]:

            # Checking, if ban permanent
            if len(punishment) == 4: # Timed ban

                # Reading values
                date_issued = punishment[1]
                duration = punishment[2]
                reason = punishment[3]

                # Calculating end date
                date = datetime.fromtimestamp(date_issued + duration)

                # Kicking player. Message contains reason and end date
                player.kick(f"Вы забанены по причине {Punishment_reasons(reason).value[1]}."
                            f" Ваш бан пройдёт {date.strftime('%d.%m.%y %H:%M:%S')}")

            else: # Permanent

                # Reading values
                reason = punishment[2]

                player.kick(f"Вы забанены навсегда по причине "
                            f"{Punishment_reasons(reason).value[1]}")

            # Logging connect reject
            wcs_logger('conn reject', f"{player.name} with {player.steamid} tried to connect"
                                      f" with {Punishment_types.BAN.name} but was rejected. "
                                      f"Reason: {Punishment_reasons(reason).name}")

        if punishment[0] == Punishment_types.MUTE.value[0]:

            # Muting player
            mute_manager.mute_player(index)