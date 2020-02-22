import discord
import random
import asyncio
import config
import logging

logger = logging.getLogger(__name__)


emoji_dict = {
    0: "0⃣",
    1: "1⃣",
    2: "2⃣",
    3: "3⃣",
    4: "4⃣",
    5: "5⃣",
    6: "6⃣",
    7: "7⃣",
    8: "8⃣",
    9: "9⃣",
    10: "🔟",
    "next": "➡",
    "back": "⬅",
    "yes": "✅",
    "no": "❌"
}

EMBED_COLOR = discord.Color(0x293984)


class MenuItem:
    def __init__(self, title, desc, value):
        self.field_data = {'name': title, 'value': desc}
        self.value = value
    
    def to_field(self):
        return self.field_data


def default_check(reaction, user):
    if user.bot:
        return False
    else:
        return True


async def _add_reactions(message, pages, page, emojis, loop=False):
    # pages = [choices[x:x + 10] for x in range(0, len(choices), 10)]
    if page > len(pages):
        page = 0
    if page:
        await message.add_reaction(str(emojis['back']))
    
    for idx, i in enumerate(pages[page], 1):
        await message.add_reaction(str(emojis[idx]))

    is_last = (page >= len(pages) - 1)
    if not is_last or (is_last and loop):
        await message.add_reaction(str(emojis['next']))
    return

def _reaction_check(check, emojis):
    def reaction_check(reaction, user):
        """Does real check first, then checks if reaction is one we're looking for"""
        if not check(reaction, user):
            return False
        return reaction.emoji in emojis.values()
    return reaction_check


async def _random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return discord.Colour.from_rgb(r, g, b)


async def _gen_embeds(pages, title=None, page_in_title=True, color=None, emojis=emoji_dict):
    embeds = []
    # pages = [choices[x:x + 10] for x in range(0, len(choices), 10)]
    if not color:
        color = await _random_color()
    for i, p in enumerate(pages):
        if page_in_title:
            t = title + f"(Page {i+1}/{len(pages)})"
        else:
            t = title
        embed = discord.Embed(title=t, colour=EMBED_COLOR)
        for i, c in enumerate(p):
            if type(c) is not dict:
                c = c.to_field()
            
            # add the emoji the user must pick
            #  (i + 1) because of zero based counting
            embed.add_field(name=emojis[i + 1] + ": " + c['name'], value=c['value'])
        embeds.append(embed)
    return embeds


async def _cleanup(m, msg="menu timed out"):
    try:
        await m.edit(content=msg, embed=None)
    except discord.Forbidden:
        await m.delete()



async def number_menu(m, choices, **kwargs):
    page = kwargs.get('page', 0)
    title = kwargs.get('title', None)
    timeout = kwargs.get('timeout', 15)
    check = kwargs.get('check', default_check)
    emojis = kwargs.get('emojis', emoji_dict)
    color = kwargs.get('color', None)
    loop = kwargs.get('loop', False)
    page_in_title = kwargs.get('page_in_title', True)
    embeds = kwargs.get('_embeds', None)

    pages = [choices[x:x + 10] for x in range(0, len(choices), 10)]
    logger.info(f"{len(pages)} pages, currently {page}")
    if not embeds:
        embeds = await _gen_embeds(pages, title=title, page_in_title=page_in_title, color=color)
        kwargs['_embeds'] = embeds

    message = await m.channel.send(embed=embeds[page])
    await _add_reactions(message, pages, page, emojis, loop)
    check = _reaction_check(check, emojis)

    try:
        reaction, user = await config.bot.wait_for('reaction_add', timeout=timeout, check=check)
    except asyncio.TimeoutError:
        await _cleanup(message)
        return message, None
    else:
        # logger.debug(f"reaction is {reaction}")
        if reaction is None:
            await _cleanup(message)
        
        reacts = {v: k for k, v in emojis.items()}
        react = reacts[reaction.emoji]

    if react == "next":
        page += 1
        # logger.debug(f"next page is now {page}")
    elif react == "back":
        page -= 1
        # logger.debug(f"back page is now {page}")
    else:
        # react is the option on the page
        try:
            # convert back to zero-based index
            p = pages[page][react - 1]
        except IndexError:
            logger.exception(f"index error with pages[{page}(page)][{react}(react)]")
            raise
        else:
            return message, p

    try:
        await message.remove_reaction(emojis[react], user)
    except discord.Forbidden:
        await message.delete()
        message = None

    kwargs['page'] = page
    return await number_menu(m, choices, **kwargs)


async def period_menu(m, name, **kwargs):
    title = kwargs.get('title', f"Select your period for {name}: ")
    timeout = kwargs.get('timeout', 15)
    check = kwargs.get('check', default_check)
    emojis = kwargs.get('emojis', emoji_dict)
    color = kwargs.get('color', None)

    if not color:
        color = await _random_color()
    embed = discord.Embed(title=title, colour=color)

    message = await m.channel.send(embed=embed)
    #0-6
    for i in range(7):
        await message.add_reaction(str(emojis[i]))
    await message.add_reaction(emojis["no"])
    check = _reaction_check(check, emojis)

    def is_valid(reaction, user):
        if not check(reaction, user):
            return False
        if reaction.emoji not in emojis.values():
            return False
        reacts = {v: k for k, v in emojis.items()}
        react = reacts[reaction.emoji]
        # logger.debug(f'reaction is {react}')
        return react in [0, 1, 2, 3, 4, 5, 6, 'no']

    try:
        reaction, user = await config.bot.wait_for('reaction_add', timeout=timeout, check=is_valid)
    except asyncio.TimeoutError:
        await _cleanup(message)
        return message, None
    else:
        # logger.debug(f"reaction is {reaction}")
        if reaction is None:
            await _cleanup(message)
        
        reacts = {v: k for k, v in emojis.items()}
        react = reacts[reaction.emoji]
        # logger.debug(f"or better known as {react}")


    if react == "no":
        # logger.debug("period cancelled")
        val = False
    else:
        val = react

    try:
        await message.remove_reaction(emojis[react], user)
    except discord.errors.Forbidden:
        await message.delete()
        message = None

    return message, val
