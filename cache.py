
import time

_store = {}
TTL = 300

def get(key):
    item = _store.get(key)
    if item and time.time() - item["ts"] < TTL:
        return item["data"]
    return None

def set(key, data):
    _store[key] = {"data": data, "ts": time.time()}
