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
CHECKMARK = lookup('BALLOT BOX WITH CHECK')
NEIGHBOUR_CATEGORY='Chat with neighbours!'
NEIGHBOUR_CHANNEL='neighbourbot'

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
        # TODO: this won't scale well if there are more than a few guilds.
        # But that's fine for now
        while True:
            for guild_client in GUILDS.values():
                await guild_client.find_chats()
                await guild_client.delete_old_channels()
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
        if message.channel.name != NEIGHBOUR_CHANNEL:
            # ignore anything that isn't a DM
            return
        elif message.author == self.user:
            # ignore messages from the bot
            return
        elif message.content.lower().startswith('match me'):
            await self.guild_client(message.guild).request_chat(message)


class GuildClient(object):
    # we have one of these for each guild and it manages everything for that guild
    def __init__(self, guild):
        self.guild = guild
        self.chats_requested = set()
        self.neighbour_channel = None
        print(f'Added guild {guild.name}')

    def get_neighbour_channel(self):
        # todo: maybe add error handling lol
        if self.neighbour_channel is None:
            self.neighbour_channel = [x for x in self.guild.channels if x.name == NEIGHBOUR_CHANNEL][0]
        return self.neighbour_channel

    def get_neighbour_category(self):
        # todo: maybe add error handling lol
        return [x for x in self.guild.categories if x.name == NEIGHBOUR_CATEGORY][0]

    async def create_and_invite_voice_channel(self):
        category = self.get_neighbour_category()
        channel_name = random_channel_name()
        channel = await category.create_voice_channel(channel_name)
        invite = await channel.create_invite()
        return invite, channel_name

    async def delete_old_channels(self):
        while True:
            category = self.get_neighbour_category()
            for channel in category.channels:
                time_since_created = datetime.now(timezone.utc) - channel.created_at.replace(tzinfo=timezone.utc)
                if time_since_created > timedelta(minutes=10) and len(channel.members) == 0:
                    await channel.delete()
            await asyncio.sleep(5)

    async def find_chats(self):
        while len(self.chats_requested) > 2:
            group = sorted(list(self.chats_requested)[:3])
            for person in group:
                self.chats_requested.remove(person)
            list_of_ids = ' and '.join([f'<@{x.id}>' for x in group])
            invite, channel_name = await self.create_and_invite_voice_channel()
            message_1 = await self.get_neighbour_channel().send(MATCH_SCRIPT.format(list_of_ids = list_of_ids, channel_name=channel_name, invite_link=str(invite)))

    async def request_chat(self, message):
        await message.add_reaction(CHECKMARK)
        self.chats_requested.add(message.author)

if __name__ == '__main__':
    client = MyClient()
    client.run(os.getenv('DISCORD_TOKEN'))
