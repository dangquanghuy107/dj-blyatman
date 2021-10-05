import re
import redis 
import youtube_dl

ydl = youtube_dl.YoutubeDL({
    'match_filter': youtube_dl.utils.match_filter_func("!is_live"),
    'age_limit': 25,
    'ratelimit': 2000000,
    'format': 'bestaudio/best',
    'extractaudio': True,
    'noplaylist': True,
    'source_address': '0.0.0.0',
    'quiet': True 
})

youtube_url_regex = '^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$'
youtube_pattern = re.compile(youtube_url_regex)

redis_client = redis.Redis(charset='utf8', decode_responses=True)

def normalize_name(input_str: str) -> str:
    output_str = input_str.replace('`', '')
    return output_str


def insult_factory(name): 
    return f"Love {name}"