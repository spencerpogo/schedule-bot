import config
import base64
import aiohttp
import logging

print('storage name is', __name__)
logger = logging.getLogger(__name__)


class JSONBinException(Exception):
    pass


class JSONBin:
    def __init__(self, secret_key=None, versioning=False, bins=tuple()):
        self.url = 'https://api.jsonbin.io/b'
        self.secret_key = {'secret-key': secret_key}
        self.bins = bins
        self.content_type = {'Content-Type': 'application/json'}
        self.versioning = versioning
        self.sess = aiohttp.ClientSession()

    async def create(self, data, collection_id=None, private=False):
        headers = self.content_type
        if self.secret_key:
            headers.update(self.secret_key)
        if collection_id:
            headers.update({'collection-id': collection_id})
        if private:
            headers.update(dict(private='true'))

        async with self.sess.post(self.url, json=data, headers=headers) as req:
            # if not await req.json()['success']:
            #     raise JSONBinException(await req.json()['message'])
            return await req.json()

    async def read(self, bin_id, bin_version='latest'):
        url = self.url + '/{}/{}'.format(bin_id, bin_version)
        headers = self.content_type
        if self.secret_key:
            headers.update(self.secret_key)

        async with self.sess.get(url, headers=headers) as req:
            try:
                req_json = await req.json()
            except Exception as err:
                raise JSONBinException(req.text, err)
            if isinstance(req_json, dict):
                if req_json.get('success') is not None:
                    if not req_json.get('sucess'):
                        raise JSONBinException(req_json)

            try:
                return await req.json()
            except Exception as err:
                raise JSONBinException(req.text, err)

    async def update(self, data, bin_id, versioning='self', like_dict=False):
        url = self.url + '/{}'.format(bin_id)
        headers = self.content_type
        if versioning == 'self':
            versioning = self.versioning

        if like_dict:
            data.update(self.read(bin_id))
        if self.secret_key:
            headers.update(self.secret_key)
        if versioning:
            headers.update(dict(versioning='true'))
        else:
            headers.update(dict(versioning='false'))

        async with self.sess.put(url, json=data, headers=headers) as req:
            j = await req.json()
            if not j['success']:
                raise JSONBinException(await req.json()['message'])

            return await req.json()

    async def delete(self, bin_id):
        url = self.url + '/{}'.format(bin_id)
        headers = self.secret_key

        async with self.sess.delete(url, headers=headers) as req:
            j = await req.json()
            if not j['success']:
                raise JSONBinException(await req.json())

            return await req.json()


SECRET = config.getenv("JKEY") or input("jsonbin secret: ")
SECRET = base64.b64decode(SECRET.encode()).decode()
BIN = config.getenv("BIN") or input("jsonbin bin id: ")

client = JSONBin(secret_key=SECRET, versioning=False)

class MultipleResults(Exception): pass
class NotFound(Exception): pass


async def with_id(i):
    i = str(i)
    def check_id(item):
        r = item['id'] == i
        logger.debug(f"{item['id']!r} == {i!r}: {r}")
        return r
    return check_id


async def get_all_users():
    data = await client.read(BIN)
    return data.get('data', [])


async def get(condition, ignore_exceptions=True):
    data = await client.read(BIN)
    #logger.debug(data)
    matches = []
    for i in data.get('data', []):
        try:
            if condition(i):
                matches.append(i)
        except:
            if not ignore_exceptions:
                raise
    # .__code__.co_name!r
    if len(matches) > 1:
        raise MultipleResults(f"{len(matches)} results for {condition}")
    elif len(matches) < 1:
        raise NotFound(f"No results found for {condition}")
    
    return matches[0]


async def get_tasks():
    data = await client.read(BIN)
    return data.get('tasks', {})


async def set_tasks(data):
    old = await client.read(BIN)
    old['tasks'] = data
    await client.update(old, BIN)


async def clear(condition, ignore_exceptions=True):
    data = await client.read(BIN)
    new = []
    for i in data.get('data', []):
        try:
            r = condition(i)
        except:
            if not ignore_exceptions:
                raise
        if not r:
            new.append(i)
        else:
            logger.debug('cleared an item')
    data['data'] = new
    await client.update(data, BIN)


async def register(obj):
    def is_duplicate(i):
        """
        # if any keys have the same value, return True
        for k in obj:
            if k in i:
                if i[k] == obj[k]:
                    logger.debug(f'key {k} is the same: {i[k]} == {obj[k]}')
                    return True
        """
        if 'id' in obj and 'id' in i:
            if i['id'] == obj['id']:
                return True
    
    await clear(is_duplicate)
    data = await client.read(BIN)
    data['data'].append(obj)
    logger.debug(f"adding object {obj}, data is now {data}")
    await client.update(data, BIN)
