import utils
import storage
import config
import tasks


async def dbg_register(m, *args):
    if m.author.id != 339943808584384512:
        return
    
    if len(args) != 4:
        return "there should be 4 args"
    _, user_string, email, pwd = args
    user = await utils.parse_member(m.channel, user_string)
    if not user:
        return "bad user"
    await storage.register({
        'id': str(user.id), 
        'em': email, 
        'pwd': pwd
    })
    return "success"


async def dbg_sharing(m, *args):
    if m.author.id != 339943808584384512:
        return
    if len(args) != 3:
        return "should be 3 args"
    _, user_string, mode = args
    user = await utils.parse_member(m.channel, user_string)
    if not user:
        return "bad user"
    
    if mode.startswith('en'):
        val = True
    else:
        val = False
    
    msg = await m.channel.send('Loading...')

    try:
        u = await storage.get(await storage.with_id(user.id))
    except storage.NotFound:
        await msg.edit(content=f"Please register with `{config.PREFIX}register` before running this command")
        return
    except storage.MultipleResults:
        storage.clear(await storage.with_id(user.id))
        await msg.edit(content=f"An unexpected error has occurred. Please register again with `{config.PREFIX}register`")
        return
    share = u.get('share', False)
    d = {
        True: 'enabled',
        False: 'disabled'
    }
    if val is None:
        await msg.edit(content=f"Sharing is {d[share]}")
        return
    
    if val == share:
        await msg.edit(content=f"Sharing is already {d[val]}")
        return
    u['share'] = val
    await storage.register(u)
    await msg.edit(content=f"Sharing successfully {d[val]}")


async def run_task(m, *args):
    if m.author.id != 339943808584384512:
        return
    #if len(args) < 2:
    #    return "ur bad"
    await tasks.run_task('signup')
    return ':ok_hand:'