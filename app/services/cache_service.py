import os
import json
from app.config import CACHE_FILE

class CacheService:

    def __init__(self):
        self.cache = self._load()

    def _load(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def save(self):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=4)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        if key in self.cache:
            self.cache[key].append(value)
        else:
            self.cache[key] = [value]
        self.save()
