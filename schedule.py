import os
import aiohttp
import datetime
import storage
import config
import logging

logger = logging.getLogger(__name__)

BASE = os.getenv("BASE") or input('base: ')
BASE2 = os.getenv('BASE2') or input('base2: ')


class APIError(Exception):
    pass


async def tryjson(r):
    import json
    try:
        j = await r.json()
    except json.JSONDecodeError:
        logger.exception(f"Error: Couldn't decode json from {r}: \n{r.text!r}")
        raise
    else:
        return j

async def trykey(j, k):
    if type(j) is not dict:
        logger.error("Error expecting json to be dict!", j)
        raise TypeError("value should be dict")
    if k not in j:
        logger.error(f"Error: expecting json to have key {k!r} {j}")
        raise KeyError(f"Value should have key {k!r}")
    return j[k]


async def process_date(date):
    if isinstance(date, datetime.datetime):
        return date.strftime('%Y-%m-%d')
    else:
        return date


async def check(v, k, expect):
    if k:
        got = await trykey(v, k)
    else:
        got = v
    if got != expect:
        s = f"{v}[{k!r}]" if k else f"{v}"
        raise APIError(f"Expected {s} to be {expect}, got {got}")


ua = {
    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12239.92.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.136 Safari/537.36"
}


class API:
    def __init__(self, em, pwd, sharing: bool=None):
        self.s = aiohttp.ClientSession()
        self.em = em
        self.pwd = pwd
        self.sharing = sharing


    async def login(self):
        # logger.debug("loggining in...")
        # login with user/pass
        async with self.s.post(BASE + '/LoginApi/Validate', json={
            "parameters": {
                "EmailAddress": self.em, "Password": self.pwd
            }
        }, headers=ua) as r:
            j = await tryjson(r)
        if 'ErrorMessages' not in j:
            raise APIError(f"Response should have errorMessages: {j}")
        if j['ErrorMessages']:
            msgs = '\n'.join(j['ErrorMessages'])
            raise APIError(f"{msgs} (Note: you have to have set your password in the web app to be able to log in! )")
        if 'IsAuthorized' not in j or not j['IsAuthorized']:
            raise APIError(f"Couldn't log into enriching students. Check your password and try again. (Note: you have to have set your password in the web app to be able to log in! )")

        vmod = await trykey(j, "ViewModel")
        token1 = await trykey(vmod, "Token1")
        token2 = await trykey(vmod, "Token2")

        # login phase2
        async with self.s.post(BASE2 + "/v1.0/login/viatokens", json={
            'token1': token1,
            'token2': token2
        }) as r:
            j = await tryjson(r)
        self.token = await trykey(j, 'authToken')
        self.headers = {
            **ua,
            'ESAuthToken': self.token,
            'Referer': BASE2 + '/dashboard'
        }
        #logger.debug('token is:', token)
        if 'errorMessage' not in j:
            raise APIError(f"Response should have errorMessage: {j}")
        if j['errorMessage']:
            msg = j['errorMessages']
            raise APIError(f"{msg}")


    async def get_schedule(self, date):
        s = self.s
        # get schedule
        # logger.debug('getting schedule...')
        async with s.post(BASE2 + '/v1.0/appointment/viewschedule', json={
            'startDate': await process_date(date)
        }, headers=self.headers) as r:
            j = await tryjson(r)
        
        # don't log as exception will be logged
        if type(j) != list:
            # logger.error('oof its not a list:', j)
            raise TypeError(f'Should be a list, got {type(j).__name__}')
        if len(j) < 1:
            # logger.error(f"Didn't get any values on {date}")
            raise APIError(f"Didn't get any values on {date}")
        # if len(j) > 1:
        #     logger.error("Got more than one value:", j)
        #     raise APIError("Too many values to process")
        # j = j[0]
        return j
    

    async def format_schedule(self, date):
        j = self.get_schedule(date)
        cdate = await trykey(j, 'scheduleDate')
        ctype = await trykey(j, 'periodDescription')
        cname = await trykey(j, 'courseName')
        return f'On {cdate} your {ctype} is {cname}'


    async def get_schedule_info(self):
        async with self.s.get(BASE2 + '/v1.0/student/setupforscheduling', headers=self.headers) as r:
            return await tryjson(r)
    

    async def get_classes(self, date):
        async with self.s.post(
            BASE2 + '/v1.0/course/forstudentscheduling', 
            json={
                'periodId': 1,
                'startDate': await process_date(date)
            },
            headers=self.headers
        ) as r:
            return await tryjson(r)
    

    async def schedule(self, date, cid, comment, method='', period=1):
        """Schedule on date with course id from a course
        ['courseId'] as returned by get_schedule()
        Set method='request' to request instead of schedule
        """
        async with self.s.post(BASE2 + f"/v1.0/appointment{method}/save", 
            json={
                'courseId': cid, #course['courseId']
                'periodId': period, #course['periodId']
                'scheduleDate': await process_date(date),
                'schedulerComment': comment
            }, headers=self.headers) as r:
                j = await tryjson(r)
        if 'appointmentRequestId' not in j:
            if 'errorMessages' not in j:
                raise APIError(f"Invalid response recieved: {j}")
            else:
                if j['errorMessages'] != []:
                    raise APIError(' '.join(j['errorMessages']))
    

    async def __aenter__(self):
        await self.login()
        return self
    
    async def __aexit__(self, etype, evalue, traceback):
        await self.s.close()


class APIHelperError(Exception): pass


async def api_helper(user, 
    register_error_msg=f"Please register with `{config.PREFIX}register` before running this command",
    unknown_error_msg=f"An unexpected error has occurred. Please register again with `{config.PREFIX}register`"):
    logger.info
    # logger.debug(user.id)
    try:
        u = await storage.get(await storage.with_id(user.id))
    except storage.NotFound:
        logger.warning("Not registered!")
        return register_error_msg
    except storage.MultipleResults:
        logger.warning("eeeee multiple results registered!")
        await storage.clear(await storage.with_id(user.id))
        return unknown_error_msg
    
    email = u['em']
    pwd = u['pwd']
    sharing = u.get('share', False)

    return API(email, pwd, sharing=sharing)
