import storage
import schedule
import utils
import config
import datetime
import time
import asyncio
import logging
from discord.utils import get

logger = logging.getLogger(__name__)


async def check_messages(user, msg):
    async for m in user.history(limit=20):
        if m.author == config.bot.user:
            if msg in m.content or m.content in msg:
                return False
    return True


async def _signup_helper(user):
    logger.info(f"Processing {user.get('id', '?')}")
    msgs = []
    auto = user.get('auto')
    if type(auto) is not list or len(auto) != 2:
        return []
    if 'em' not in user or 'pwd' not in user or 'id' not in user:
        return ["Couldn't sign you up because your registration data is invalid. ",
                "Try registering again. "]
    pattern, comment = auto
    async with schedule.API(user['em'], user['pwd']) as api:
        date = datetime.datetime.now()
        # next 4 tuesday/thursdays (2 weeks)
        for _ in range(4):
            # get next_dt using the day after the last one
            date = await utils.next_dt(today=date + datetime.timedelta(days=1))
            ds = date.strftime("%m/%d")
            cls = await api.get_schedule(date)
            c = [i for i in cls if str(i.get('periodId')) == '1']
            if len(c) != 1:
                raise ValueError(f"There should only be one period 1: {cls} produces {c}")
            c = c[0]
            if c['courseName'] != 'Open Schedule':
                logger.info(f"On {ds} user is already signed up")
                continue
            courses = await api.get_classes(date)
            logger.info(f'Processing for {ds}...')
            items = await utils.process_courses(courses['courses'])
            for i in items:
                v = i.value
                if pattern in v['name'].lower():
                    if v['reqCid'] == v['cid']:
                        logger.info('Pattern found but course already requested. ')
                        continue
                    logger.info(f"Scheduling {v['name']}...")
                    await api.schedule(date, v['cid'], comment,
                        method=v['method'], period=v['period'])
                    action = v['method']+'ed' if v['method'] else 'scheduled'
                    msgs.append(f":white_check_mark: Successfully {action} you for {v['name']} on {ds}")
    return msgs


async def auto_signup():
    # get all users
    data = await storage.get_all_users()
    for entry in data:
        r = await _signup_helper(entry)
        msg = "\n".join(r)
        if not msg:
            continue
        i = int(entry.get('id', '1234'))
        members = config.bot.get_all_members()
        user = get(members, id=i)
        if not user:
            logger.info('user not found')
            continue
        try:
            send = await check_messages(user, msg)
        except:
            logger.exception("Error swallowed while checking message history for {user}")
            send = False
        if send:
            logger.info(f'sending {msg!r} to {i}...')
            await user.send(msg)
        else:
            logger.info("not sending {msg!r} to {i}")


FUNCS = {
    'signup': auto_signup
}


TASKS = {
    'signup': 30*60
}


async def run_task(name, data=None):
    if name not in FUNCS:
        raise ValueError(f"task {name} not in funcs")
    if data is None:
        data = await storage.get_tasks()
    await FUNCS[name]()
    t = time.time()
    data[name] = t
    await storage.set_tasks(data)
    logger.info('Tasks updated. ')


async def run_new_tasks():
    logger.info('Checking for new tasks...')
    task_data = await storage.get_tasks()
    diffs = []
    for name, interval in TASKS.items():
        if name not in FUNCS:
            raise ValueError(f"Function {name!r} not in FUNCS")
        last = task_data.get(name, 0)
        diff = time.time() - last

        # if time since last run is less than how often we want to run it
        if diff < interval:
            # save the time left and skip
            logger.debug(f'last is {last}, diff is {diff}')
            diffs.append(diff)
            continue

        await run_task(name)
        diffs.append(interval)
    if not diffs:
        return 0
    logger.info(str(diffs))
    return min(diffs)



async def main():
    while True:
        try:
            t = await run_new_tasks()
            logger.info(f'sleeping for {t}')
            # wait at least 15 secs or t
            await asyncio.sleep(t)
        except:
            logger.exception("Exception in tasks! ")
            await asyncio.sleep(5)
            


def start(loop):
    for name in TASKS.keys():
        if name not in FUNCS:
            raise ValueError(f"Function {name!r} not in FUNCS")
    loop.create_task(main())