import config
import datetime

DOM = config.getenv("IXL_DOM")
LOGIN_PATH = config.getenv("IXL_LOGIN_PATH")


class InvalidLoginError(Exception): pass


async def check_status(name, r, expect=200):
    if r.status != expect:
        text = await r.text()
        raise ValueError(f"{name} returned status {r.status}: \n{text}")


async def tryjson(r, **kwargs):
    import json
    try:
        j = await r.json(**kwargs)
    except json.JSONDecodeError:
        raise ValueError(f"Error: Couldn't decode json from {r}: \n{r.text!r}")
    else:
        return j


async def trykeys(j, *keys):
    for k in keys:
        if type(j) is not dict:
            raise TypeError("Error expecting object to be dict instead got: " + str(j))
        if k not in j:
            raise KeyError(f"Error: expecting object to have key {k!r} {j}")
        j = j[k]
    return j


async def process_date(date):
    if isinstance(date, datetime.datetime):
        return date.strftime('%Y-%m-%d')
    else:
        return str(date)


async def login(s, user, pwd):
    async with s.get(DOM + LOGIN_PATH, params={
        'accountHeaderId': '1442828',
        'username': user,
        'password': pwd,
        '__checkbox_rememberUser': 'true'
    }, allow_redirects=False) as r:
        if r.status != 302:
            raise InvalidLoginError("Login invalid")


async def get_stats(s, start_date, end_date=None, 
    low_grade=-2, high_grade=12, 
    subjects=0, time_period=10):
    start_date = await process_date(start_date)
    if end_date is None:
        end_date = datetime.datetime.now()
    end_date = await process_date(end_date)
    async with s.get(
        "https://www.ixl.com/analytics/student-details/run", params={
            'subjects': str(subjects),
            'lowGrade': str(low_grade),
            'highGrade': str(high_grade),
            'startDate': start_date,
            'endDate': end_date,
            'timePeriod': str(time_period)
        }) as r:
        await check_status("stats", r)
        return await tryjson(r, content_type=None)
