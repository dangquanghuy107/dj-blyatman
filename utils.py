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

def normalize_name(input_str):
    s1 = u' ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u' AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    s = ''
    remove_specialCharacter = ''.join(e for e in input_str if e.isalnum())
    for c in remove_specialCharacter:
        if c in s1:
            s += s0[s1.index(c)]
        else:
            s += c
    return s


def insult_factory(name): 
    return f"Love {name}"