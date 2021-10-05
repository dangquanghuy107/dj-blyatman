from dotenv import load_dotenv
import os 

load_dotenv()

MUSIC_QUEUE = "music_queue"
TOKEN = os.getenv("TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL")