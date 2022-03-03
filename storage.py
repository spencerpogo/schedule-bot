import config
import json
import logging

logger = logging.getLogger(__name__)

class MultipleResults(Exception): pass
class NotFound(Exception): pass


DB_FILENAME = config.getenv("DB_FILE") or "db.json"


async def read():
    with open(DB_FILENAME, "r") as f:
        data = f.read()
    return json.loads(data)


async def update(newdata):
    with open(DB_FILENAME, "w+") as f:
        f.write(json.dumps(newdata))



async def with_id(i):
    i = str(i)
    def check_id(item):
        r = item['id'] == i
        return r
    return check_id


async def get_all_users():
    data = await read()
    return data.get('data', [])


async def get(condition, ignore_exceptions=True):
    data = await read()
    matches = []
    for i in data.get('data', []):
        try:
            if condition(i):
                matches.append(i)
        except Exception as e:
            if not ignore_exceptions:
                raise e
    if len(matches) > 1:
        raise MultipleResults(f"{len(matches)} results for {condition}")
    elif len(matches) < 1:
        raise NotFound(f"No results found for {condition}")
    
    return matches[0]


async def get_tasks():
    data = await read()
    return data.get('tasks', {})


async def set_tasks(data):
    old = await read()
    old['tasks'] = data
    await update(old)


async def clear(condition, ignore_exceptions=True):
    data = await read()
    new = []
    for i in data.get('data', []):
        try:
            r = condition(i)
        except Exception:
            if not ignore_exceptions:
                raise
        if not r:
            new.append(i)
    data['data'] = new
    await update(data)


async def register(obj):
    def is_duplicate(i):
        if 'id' in obj and 'id' in i:
            if i['id'] == obj['id']:
                return True
    
    await clear(is_duplicate)
    data = await read()
    data['data'].append(obj)
    await update(data)
