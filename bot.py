import asyncio
from locale import normalize
import logging
import json

import discord
from discord import channel
from discord import player
from discord.ext import commands

from utils import (ydl, youtube_pattern, insult_factory, normalize_name,
                            redis_client)
from models import RedisQueue
from reply import * 
from config import TOKEN, LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)
bot = commands.Bot(command_prefix=commands.when_mentioned_or("."), description=BOT_DESCRIPTION)
queue = RedisQueue()
# queue.clear()

@bot.event
async def on_ready():
    print("Bot is ready!")


@bot.event 
async def on_message(message):
    if bot.user.mentioned_in(message):
        await message.channel.send(ON_MENTION)


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

    def after_playing(self, data_for_repeat, ctx: commands.Context) -> None: 
        if redis_client.get("repeat") == "on": 
            logging.info("Repeat")
            player = YoutubeAudioSource.from_data(data_for_repeat)
            ctx.voice_client.play(player, after=lambda e: logging.error(e) if e else self.after_playing(data_for_repeat, ctx=ctx))
            return 

        logging.info("Next song")
        if queue.is_empty(): 
            return 

        message = json.loads(queue.pop())
        player = YoutubeAudioSource.from_data(message)

        ctx.voice_client.play(player, after=lambda e: logging.error(e) if e else self.after_playing(message, ctx=ctx))
        return 

    async def play_from_text(self, ctx: commands.Context, text, user_id): 
        async with ctx.typing(): 
            data = await YoutubeAudioSource.get(text, loop=self.bot.loop, data_only=True)
            
        is_playing = ctx.voice_client.is_playing()

        if is_playing:
            data = json.dumps(data)
            queue.push(data)
            await ctx.send(PLAY_ADD_TO_QUEUE)
        else: 
            player = YoutubeAudioSource.from_data(data)
            ctx.voice_client.play(player, after=lambda e: logging.error(e) if e else self.after_playing(data, ctx=ctx))
            await ctx.send(PLAY_OK + f"`{normalize_name(data['title'])}`")

    @commands.command(aliases=['p'], brief='Play the music', description='Play the music using Youtube search keyword or Youtube URL') 
    async def play(self, ctx: commands.Context, *, url_or_text=None): 
        if not url_or_text: 
            return await ctx.send(PLAY_NO_URL_OR_TEXT)

        if not ctx.author.voice:
            # User didn't connect to any voice channel
            return await ctx.send(PLAY_NO_CHANNEL)
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            # User's already connect to a different voice channel
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        is_url = youtube_pattern.match(url_or_text)
        user_id = ctx.author.id

        if is_url: 
            return await self.play_from_text(ctx, url_or_text, user_id)
        else: 
            return await self.play_from_text(ctx, f"ytsearch:{url_or_text}", user_id)

    @commands.command(brief="Stop the music", description="This command will stop the music and clear the queue.")
    async def stop(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send(STOP_NO_MUSIC)
        else: 
            is_playing = ctx.voice_client.is_playing() 
            if not is_playing:
                await ctx.send(STOP_NO_MUSIC)
            else: 
                queue.clear()
                ctx.voice_client.stop()
                await ctx.send(STOP)

    @commands.command(brief="Change repeat mode", description="Set the repeat mode to on/off")
    async def repeat(self, ctx: commands.Context, mode: str = None): 
        if not mode: 
            return await ctx.send(REPEAT_NO_MODE)

        mode = mode.lower().strip()
        if mode not in ['on', 'off']:
            return await ctx.send(REPEAT_INVALID_MODE.format(mode=mode))

        redis_client.set("repeat", mode)
        await ctx.send(REPEAT_OK.format(mode=mode))

    @commands.command(aliases=['fs'], brief='Skip to next song in queue') 
    async def skip(self, ctx: commands.Context): 
        if not ctx.voice_client:
            await ctx.send(STOP_NO_MUSIC)
        else: 
            is_playing = ctx.voice_client.is_playing() 
            if not is_playing:
                await ctx.send(STOP_NO_MUSIC)
            else: 
                ctx.voice_client.stop()
                await ctx.send(STOP)

    @commands.command(aliases=['q'], brief='Get current queue') 
    async def get_queue(self, ctx: commands.Context):
        if queue.is_empty():
            return await ctx.send(GET_QUEUE_EMPTY) 

        embed = discord.Embed()

        queue_items = queue.list_all()
        result = [item['title'] for item in queue_items]
        result_str = '\n'.join(f'{id + 1}. {normalize_name(item)}' for id, item in enumerate(result))

        embed.add_field(name=QUEUE_NAME, value=result_str)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=['clear'], brief='Clear current queue') 
    async def clear_queue(self, ctx: commands.Context):
        queue.clear() 
        await ctx.send(CLEAR_QUEUE)

    @commands.command(aliases=['insult'], brief='Insult someone', description='Usage: .curse @someone') 
    async def curse(self, ctx, user):
        message = insult_factory(user)
        await ctx.send(message)

    @commands.command(aliases=['dc'], brief='Disconnect from voice channel')
    async def disconnect(self, ctx):
        if not ctx.voice_client: 
            return 

        queue.clear() 
        redis_client.set("repeat", "off")

        await ctx.voice_client.disconnect()


bot.add_cog(MusicCog(bot))
bot.run(TOKEN)
