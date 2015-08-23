#!C:/Python34/python.exe -u

from sys import exit
from config.config import config
import lib.bot as bot

# Twitch Plays
# Inpsired by http://twitch.tv/twitchplayspokemon
# Written by Aidan Thomson - <aidraj0 at gmail dot com>

try:
    bot.Bot().run()
except KeyboardInterrupt:
    exit()
