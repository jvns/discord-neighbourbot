# bot.py
import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
import discord
import asyncio
from unicodedata import lookup

MATCH_SCRIPT="""
{list_of_ids} are neighbours! Go chat in **#{channel_name}** {invite_link} !
"""
CHECKMARK = '☑️'
NEIGHBOUR_CATEGORY='Chat with neighbours!'
NEIGHBOUR_CHANNEL='neighbourbot'
NEIGHBOURBOT_TOPIC="""say "**match me**" to get matched with 2 other people to voice chat with.
It's like chatting with the person next to you at a conference!"""

def read_words(filename):
    with open(filename) as f:
        return [x.strip() for x in f.readlines()]

computer_words = read_words('computer.txt')
flower_words = read_words('flowers.txt')

def random_channel_name():
    return random.choice(computer_words) + '-' + random.choice(flower_words)

# make this a global for now because we can't set attributes on the discord client
GUILDS = dict()

class MyClient(discord.Client):
    def __init__(self):
        super().__init__()

    async def run_guild_tasks(self):
        # Go through every server (guild) we're connected to and do everything
        # that needs to be done
        while True:
            tasks = []
            for guild in self.guilds:
                guild_client = self.guild_client(guild)
                tasks.append(guild_client.get_neighbour_channel())
                tasks.append(guild_client.find_chats())
                tasks.append(guild_client.delete_old_channels())
            asyncio.gather(*tasks)
            await asyncio.sleep(2)

    def guild_client(self, guild):
        if guild not in GUILDS:
            GUILDS[guild] = GuildClient(guild)
        return GUILDS[guild]

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        # delete old channels in the background
        await self.run_guild_tasks()

    async def on_message(self, message):
        if message.author == self.user:
            # ignore messages from the bot
            return
        elif type(message.channel) == discord.DMChannel:
            await message.channel.send("talk to me in the #neighbourbot channel instead!")
            return
        elif message.channel.name != NEIGHBOUR_CHANNEL:
            # ignore anything that isn't a DM
            return
        elif message.content.lower().startswith('match me'):
            await self.guild_client(message.guild).request_chat(message)


class GuildClient(object):
    # we have one of these for each guild and it manages everything for that guild
    def __init__(self, guild):
        self.guild = guild
        self.chats_requested = set()
        self.neighbour_channel = None
        self.neighbour_category = None
        print(f'Added guild {guild.name}')

    async def get_neighbour_channel(self):
        matches = [x for x in self.guild.channels if x.name == NEIGHBOUR_CHANNEL]
        if len(matches) == 0:
            # by default put the channel in the guild's first category
            category = self.guild.categories[0]
            return await category.create_text_channel(NEIGHBOUR_CHANNEL, topic=NEIGHBOURBOT_TOPIC)
        else:
            return matches[0]

    async def get_neighbour_category(self):
        matches = [x for x in self.guild.categories if x.name == NEIGHBOUR_CATEGORY]
        if len(matches) == 0:
            return await self.guild.create_category(NEIGHBOUR_CATEGORY)
        else:
            return matches[0]

    async def create_and_invite_voice_channel(self):
        category = await self.get_neighbour_category()
        channel_name = random_channel_name()
        channel = await category.create_voice_channel(channel_name)
        invite = await channel.create_invite()
        return invite, channel_name

    async def delete_old_channels(self):
        category = await self.get_neighbour_category()
        for channel in category.channels:
            time_since_created = datetime.now(timezone.utc) - channel.created_at.replace(tzinfo=timezone.utc)
            if time_since_created > timedelta(minutes=10) and len(channel.members) == 0:
                await channel.delete()

    async def find_chats(self):
        while len(self.chats_requested) >= 2:
            if len(self.chats_requested) == 4:
                group = list(self.chats_requested)[:2]
            else:
                group = list(self.chats_requested)[:3]
            for person in group:
                self.chats_requested.remove(person)
            list_of_ids = ' and '.join([f'<@{x.id}>' for x in group])
            invite, channel_name = await self.create_and_invite_voice_channel()
            neighbour_channel = await self.get_neighbour_channel()
            await neighbour_channel.send(MATCH_SCRIPT.format(list_of_ids = list_of_ids, channel_name=channel_name, invite_link=str(invite)))

    async def request_chat(self, message):
        await message.add_reaction(CHECKMARK)
        self.chats_requested.add(message.author)

if __name__ == '__main__':
    client = MyClient()
    client.run(os.getenv('DISCORD_TOKEN'))
