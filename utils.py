import re
import json
from extensions import r

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def get_cached_persons():
    if r:
        cached = r.get('persons')
        if cached:
            return json.loads(cached)
    return None

def cache_persons(persons_list):
    if r:
        r.setex('persons', 300, json.dumps(persons_list))

def invalidate_persons_cache():
    if r:
        r.delete('persons')
