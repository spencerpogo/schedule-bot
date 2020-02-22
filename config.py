import discord
import os

PREFIX="s!"
embed_color = None
bot = discord.Client()

def getenv(key, default=None):
    """Gets env vars. If MODE is dev, tries to get key_DEV otherwise just returns key"""
    suffix = ''
    if os.getenv('MODE').lower() == 'dev':
        suffix = '_DEV'
    val = os.getenv(key + suffix, None)
    if val is None:
        print(key+suffix, "didn't exist, got", key)
        return os.getenv(key, default)
    print('got', key+suffix)
    return os.getenv(key + suffix, default)
