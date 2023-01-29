# ../WCSSkills/wcs/xp.py
"""
This file registers events, and gives XP for that
using implemented method .add_xp(amount, reason) in WCS_Player class
"""

# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports

# Source.Python Imports
# Event
from events import Event

# WCS_Players dictionary
from .WCSP.wcsplayer import WCS_Player, WCS_Players

# =============================================================================
# >> All
# =============================================================================

__all__ = (
    'round_start',
    'round_end',
    'player_death',
    'bomb_planted',
    'bomb_exploded',
    'bomb_defused'
)


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
    killer = WCS_Player.from_userid(ev['attacker'])

    # try: victim = WCS_Players[ev['userid']]
    # except KeyError: victim = None

    assister = WCS_Player.from_userid(ev['assister'])

    is_headshot = ev['headshot']

    if killer is not None:

        multiplier = killer.xp_multiplier
        if is_headshot:
            multiplier += 1
            head = ' в голову'
        else: head = ''

        if ev['weapon'] == 'elite':
            killer.add_xp(40*multiplier, f'убийство беретами{head}')
        elif ev['weapon'] == 'hkp2000':
            killer.add_xp(50*multiplier, f'убийство с P2000{head}')
        elif ev['weapon'] == 'glock':
            killer.add_xp(50*multiplier, f'убийство с глока{head}')
        elif ev['weapon'] == 'p250':
            killer.add_xp(40*multiplier, f'убийство с P250{head}')
        elif ev['weapon'] == 'revolver':
            killer.add_xp(50*multiplier, f'убийство с револьвера')
        elif ev['weapon'] == 'ainferno' or ev['weapon'] == 'inferno':
            killer.add_xp(70*multiplier, 'убийство молотовым')
        elif ev['weapon'] == 'hegrenade':
            killer.add_xp(70*multiplier, 'убийство гранатой')
        elif ev['weapon'] == 'taser':
            killer.add_xp(100*multiplier, 'убийство \2шокером\1')
        elif ev['weapon'] == 'knife' or ev['weapon'] == 'knife_t':
            killer.add_xp(100*multiplier, 'убийство \2ножом\1')
        else:
            killer.add_xp(30*multiplier, f'убийство{head}')

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
