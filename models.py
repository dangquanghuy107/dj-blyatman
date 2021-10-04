from typing import List

import redis 

import json

from youtube_dl.utils import US_RATINGS
from music_bot.config import MUSIC_QUEUE


class RedisQueue(object): 
    def __init__(self):
        self.client = redis.Redis() 
    
    def push(self, message: str) -> None:
        self.client.rpush(MUSIC_QUEUE, message)

    def pop(self) -> str:
        message = self.client.lpop(MUSIC_QUEUE)
        return message

    def size(self) -> int: 
        return self.client.llen(MUSIC_QUEUE)
    
    def list_all(self) -> List[str]: 
        queue_items = self.client.lrange(MUSIC_QUEUE, 0, -1)
        result = [json.loads(item) for item in queue_items]

        return result 

    def clear(self) -> None: 
        self.client.delete(MUSIC_QUEUE)

    def is_empty(self) -> bool: 
        return self.size() == 0 