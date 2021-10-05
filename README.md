# dj-blyatman

## Setup 
- No time == No dockerization yet

### Redis
- Install redis: 
```
sudo apt update
sudo apt install redis-server -y

sudo systemctl enable redis-server
```
- Config redis by editing `/etc/redis/redis.conf`
- Restart redis after configuration: `sudo systemctl restart redis-server`

### Python
- Install requirements
```
pip install -r requirements.txt
```
- Create a bunch of replies to your liking by creating `reply.py` with the contents in `reply.py.sample`
- Run the bot 
```
python bot.py
```