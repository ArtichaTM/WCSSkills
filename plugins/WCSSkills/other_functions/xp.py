# ../WCSSkills/wcs/xp
"""
This file registers events, and gives XP for that
using implemented method .add_xp(amount, reason) in WCS_Player class
"""

# =============================================================================
# >> IMPORTS
# =============================================================================

# Event
from events import Event

# WCS_Players dictionary
from WCSSkills.wcs.wcsplayer import WCS_Players

# =============================================================================
# >> Events to give XP
# =============================================================================

@Event('round_freeze_end')
def round_start(_):
    for player in WCS_Players.values():
        player.add_xp(10*player.xp_multiplier, 'начало раунда')

@Event('round_end')
def round_end(_):
    for player in WCS_Players.values():
        player.add_xp(10*player.xp_multiplier, 'конец раунда')

@Event('player_death')
def player_death(ev):

    # Loading parameters, and checking if parameter is players (not bots)
    try: killer = WCS_Players[ev['attacker']]
    except KeyError: return

    try: victim = WCS_Players[ev['userid']]
    except KeyError: victim = None

    try: assister = WCS_Players[ev['assister']]
    except KeyError: assister = None

    is_headshot = ev['headshot']
    multiplier = killer.xp_multiplier
    if is_headshot:
        multiplier += 1

    if killer is not None:
        if ev['weapon'] == 'elite':
            killer.add_xp(40*multiplier, 'убийство берретами')
        elif ev['weapon'] == 'hkp2000':
            killer.add_xp(50*multiplier, 'убийство с P2000')
        elif ev['weapon'] == 'glock':
            killer.add_xp(50*multiplier, 'убийство с глока')
        elif ev['weapon'] == 'p250':
            killer.add_xp(40*multiplier, 'убийство с P250')
        elif ev['weapon'] == 'revolver':
            killer.add_xp(50*multiplier, 'убийство с револьвера')
        elif ev['weapon'] == 'ainferno':
            killer.add_xp(70*multiplier, 'убийство молотовым')
        elif ev['weapon'] == 'inferno':
            killer.add_xp(70*multiplier, 'убийство молотовым')
        elif ev['weapon'] == 'hegrenade':
            killer.add_xp(70*multiplier, 'убийство гранатой')
        elif ev['weapon'] == 'taser':
            killer.add_xp(100*multiplier, 'убийство \2шокером\1')
        elif ev['weapon'] == 'knife' or ev['weapon'] == 'knife_t':
            killer.add_xp(100*multiplier, 'убийство \2ножом\1')
        else:
            killer.add_xp(30*multiplier, 'убийство')

    if assister is not None:
        assister.add_xp(15, 'помощь')

@Event('bomb_planted')
def bomb_planted(ev):
    for player in WCS_Players.values():

        # Give xp to planter
        if player.userid == ev['userid']:
            player.add_xp(25*player.xp_multiplier, 'установку бомбы')
            continue

        # Give xp to terrorist team
        if player.team == 2:
            if player.is_dead:
                player.add_xp(3*player.xp_multiplier, 'установку бомбы вашим союзником')
            else:
                player.add_xp(5*player.xp_multiplier, 'установку бомбы вашим союзником')
            continue

@Event('bomb_exploded')
def bomb_exploded(_):
    for player in WCS_Players.values():

        # Give xp to terrorist team
        if player.team == 2:
            if player.is_dead:
                player.add_xp(10*player.xp_multiplier, 'взрыв бомбы')
            else:
                player.add_xp(14*player.xp_multiplier, 'взрыв бомбы')
            continue

@Event('bomb_defused')
def bomb_defused(ev):
    for player in WCS_Players.values():

        # Give xp to ct, that defused c4
        if player.userid == ev['userid']:
            player.add_xp(25*player.xp_multiplier, 'обезвреживание бомбы')

        elif player.team == 3:
            if player.is_dead:
                player.add_xp(3*player.xp_multiplier, 'обезвреживание бомбы вашим союзником')
            else:
                player.add_xp(5*player.xp_multiplier, 'обезвреживание бомбы вашим союзником')