import asyncio
from locale import normalize
import logging
import json

import discord
from discord import channel
from discord import player
from discord.ext import commands

from music_bot.utils import ydl, youtube_pattern, insult_factory
from music_bot.models import RedisQueue
from music_bot.reply import * 

logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='.', description='DJ Blyatman')
queue = RedisQueue()
queue.clear()

@bot.event
async def on_ready():
    print("Bot is ready!")


class YoutubeAudioSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5): 
        super().__init__(source, volume)
        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    def from_data(cls, data):
        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, options='-vn'), data=data)

    @classmethod
    async def get(cls, text, *, loop=None, data_only=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(text, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        if data_only:
            return data 
        else: 
            return cls(discord.FFmpegPCMAudio(filename, options='-vn'), data=data), data


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 

    def after_playing(self, ctx: commands.Context) -> None: 
        logging.info("Next song")
        if queue.is_empty(): 
            return 

        message = json.loads(queue.pop())
        player = YoutubeAudioSource.from_data(message)

        ctx.voice_client.play(player, after=lambda e: logging.error(e) if e else self.after_playing(ctx=ctx))
        return 

    async def play_from_text(self, ctx: commands.Context, text, user_id): 
        async with ctx.typing(): 
            data = await YoutubeAudioSource.get(text, loop=self.bot.loop, data_only=True)
            data["title"] = normalize(data["tilte"])

        is_playing = ctx.voice_client.is_playing()

        if is_playing:
            data = json.dumps(data)
            queue.push(data)
            await ctx.send(PLAY_ADD_TO_QUEUE)
        else: 
            player= YoutubeAudioSource.from_data(data)
            ctx.voice_client.play(player, after=lambda e: logging.error(e) if e else self.after_playing(ctx=ctx))
            await ctx.send(PLAY_OK + f"`{data['title']}`")

    @commands.command() 
    async def play(self, ctx: commands.Context, *, url_or_text=None): 
        if not ctx.author.voice:
            # User didn't connect to any voice channel
            return await ctx.send(PLAY_NO_CHANNEL)
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            # User's already connect to a different voice channel
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        if not url_or_text: 
            return await ctx.send(PLAY_NO_URL_OR_TEXT)

        is_url = youtube_pattern.match(url_or_text)
        user_id = ctx.author.id

        if is_url: 
            return await self.play_from_text(ctx, url_or_text, user_id)
        else: 
            return await self.play_from_text(ctx, f"ytsearch:{url_or_text}", user_id)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send(STOP_NO_MUSIC)
        else: 
            is_playing = ctx.voice_client.is_playing() 
            if not is_playing:
                await ctx.send(STOP_NO_MUSIC)
            else: 
                ctx.voice_client.stop()
                await ctx.send(STOP)

    @commands.command() 
    async def get_queue(self, ctx: commands.Context): 
        queue_items = queue.list_all()
        result = [item['title'] for item in queue_items]
        import json
        await ctx.send(json.dumps(result))
    
    @commands.command() 
    async def clear_queue(self, ctx: commands.Context):
        queue.clear() 
        await ctx.send("Queue cleared")

    @commands.command() 
    async def curse(self, ctx, user):
        message = insult_factory(user)
        await ctx.send(message)

    @commands.command()
    async def dc(self, ctx):
        if not ctx.voice_client: 
            return 
        await ctx.voice_client.disconnect()


bot.add_cog(MusicCog(bot))
bot.run(YOUR_TOKEN)