"""Schedule bot v1.6"""
#raise
import os
print(f"Starting in mode {os.getenv('MODE')!r}...")
import time
start = time.time()
import discord
import cmds as cmd_funcs
import admin as admin_cmds
import web
import config
import tasks
from schedule import APIError
import traceback
import asyncio
import sys
import logging
import logging.handlers

version = 'v1.6'

# LOGGING
root = logging.getLogger()
logger = logging.getLogger('main')
root.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')

def logfilter(record):
    print(record.name)
    return 0
root.addFilter(logfilter)

# one file for every day
fh = logging.handlers.TimedRotatingFileHandler(os.path.abspath('./logs/bot.log'),               when='midnight', backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
root.addHandler(fh)

seh = logging.StreamHandler()
seh.setLevel(logging.DEBUG)
seh.setFormatter(formatter)
root.addHandler(seh)

for i in ['discord', 'websockets']:
    l = logging.getLogger(i)
    l.setLevel(logging.INFO)
    l.addHandler(seh)

soh = logging.StreamHandler(stream=sys.stdout)
soh.setLevel(logging.DEBUG)
soh.setFormatter(formatter)
logger.addHandler(soh)
# END LOGGING


bot = config.bot
WHITELISTED_GUILDS = [int(i) for i in config.getenv("guilds").split(",")]

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="with APIs | s!help", type=3))
    startup = time.time() - start
    logger.info(f"Logged in as {bot.user} in {startup:.1f}s")


CMDS = [
    {
        'name': 'class',
        'usage': 'class [date] [user=username, mention or ID]',
        'desc': 'Gets your scheduled class on the next tuesday/thursday or a custom date',
        'func': cmd_funcs.cls
    },
    {
        'name': 'register',
        'usage': 'register email pwd',
        'desc': 'Registers your email and password with the bot',
        'func': cmd_funcs.register
    },
    {
        'name': 'list',
        'usage': 'list [date]',
        'desc': 'shows a menu of the available ',
        'func': cmd_funcs.c_list
    },
    {
        'name': 'sharing',
        'usage': 'sharing OR {PRE}sharing enable|disable',
        'desc': 'shows or sharing setting or changes it',
        'func': cmd_funcs.sharing
    },
    {
        'name': 'auto',
        'usage': 'auto OR {PRE}auto pattern comment',
        'desc': 'shows your auto sharing configuration or sets auto sharing to trigger on pattern and gin up with comment',
        'func': cmd_funcs.auto
    },
    {
        'name': 'ping',
        'usage': 'ping',
        'desc': 'Shows latency',
        'func': cmd_funcs.pong
    },
    {
        'name': 'dbg_register',
        'func': admin_cmds.dbg_register
    },
    {
        'name': 'dbg_sharing',
        'func': admin_cmds.dbg_sharing
    },
    {
        'name': 'task',
        'func': admin_cmds.run_task
    }
]


async def run_cmd(cmd, m):
    for c in CMDS:
        if c['name'] == cmd:
            logging.info(f'{m.author} is running {cmd}')
            args = m.content.strip().split(" ")
            async with m.channel.typing():
                r = await c['func'](m, *args)
                if r:
                    if isinstance(r, discord.Embed):
                        await m.channel.send(embed=r)
                    else:
                        await m.channel.send(r)
            


async def help_cmd(m, bot):
    s = ["**Note**: [date] is optional, if not supplied it will default to next"
    "tuesday/thursday. Date can be a weekday (like \"thursday\") or a date"
    " (like \"10/08\")\n**You must have changed you password on the website, there is no default!** To set your password, log in to the web app with google, go to manage password, and change your password. \n"
    "If you still have issues logging in, contact Scoder12"]
    for c in CMDS:
        if 'usage' not in c or 'desc' not in c:
            continue
        s.append(f"`{config.PREFIX}{c['usage'].replace('{PRE}', config.PREFIX)}` {c['desc']}")
    
    s.append("**This bot is in beta. If you encounter any bugs please contact Scoder12.**")
    embed = discord.Embed(title="Help", description="\n".join(s))
    embed.set_footer(text=f"Schedule bot {version}")
    return embed


CMDS.append({
    'name': 'help',
    'usage': 'help',
    'desc': 'shows help',
    'func': help_cmd
})


@bot.event
async def on_message(m):
    if m.author.id == bot.user:
        return
    if m.guild is not None:
        if m.guild.id not in WHITELISTED_GUILDS:
            logger.warn(f'bad guild: {m.guild.id!r}')
            return

    if m.content.startswith(config.PREFIX):
        cmd = m.content[len(config.PREFIX):].split(" ")[0]
        try:
            await run_cmd(cmd, m)
        except Exception as e:
            if isinstance(e, APIError):
                logger.exception("API error in cmd {cmd}: ")
                await m.channel.send("Enriching Students API error: " + str(e))
            else:
                logger.exception("Error in cmd {cmd}: ")
                await m.channel.send("```\n" + traceback.format_exc() + "\n```")
    

if __name__ == '__main__':
    print("Running...")
    logger.info("\n\n-----RESTART-----\n\n")
    logger.info(f"Schedule bot v{version} starting...")
    loop = asyncio.get_event_loop()
    loop.create_task(web.run())
    tasks.start(loop)
    bot.run(config.getenv('TOKEN') or input("token: "))