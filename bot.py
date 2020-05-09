# bot.py
import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
import discord
import asyncio
from unicodedata import lookup

MATCH_SCRIPT="""
I've matched you with {list_of_ids}! Go chat in **#{channel_name}** {invite_link} !
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
                tasks.append(guild_client.delete_old_channels())
            asyncio.gather(*tasks)
            await asyncio.sleep(60)

    def guild_client(self, guild):
        if guild not in GUILDS:
            GUILDS[guild] = GuildClient(guild)
        return GUILDS[guild]

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        # delete old channels in the background
        await self.run_guild_tasks()

    async def on_message(self, message):
        content = message.content.lower()
        if message.author == self.user:
            # ignore messages from the bot
            return
        elif type(message.channel) == discord.DMChannel:
            await message.channel.send("talk to me in the #neighbourbot channel instead!")
            return
        elif message.channel.name != NEIGHBOUR_CHANNEL:
            # ignore anything that isn't a DM
            return
        elif 'match me' in content and '"match me"' not in content and "'match me'" not in content:
            await self.guild_client(message.guild).request_chat(message)


class GuildClient(object):
    # we have one of these for each guild and it manages everything for that guild
    def __init__(self, guild):
        self.guild = guild
        self.chats_requested = set()
        self.neighbour_channel = None
        self.neighbour_category = None
        self.match_in_progress = False
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

    async def send_intro(self, intros, person, other_person):
        if intros is None:
            # there's no #introductions channel, give up
            return
        intro = intros.get(other_person, None)
        if intro is None:
            # we don't have an intro for that person
            return
        await person.send(f"@{other_person.name}, from #introductions: \"{intro}\"")

    async def find_chats(self):
        all_people = self.chats_requested.copy()
        intros = await self.get_introductions()
        while len(self.chats_requested) >= 2:
            if len(self.chats_requested) == 4:
                group = list(self.chats_requested)[:2]
            else:
                group = list(self.chats_requested)[:3]
            for person in group:
                self.chats_requested.remove(person)
            invite, channel_name = await self.create_and_invite_voice_channel()
            neighbour_channel = await self.get_neighbour_channel()
            for person in group:
                other_people = [x for x in group if x != person]
                list_of_ids = ' and '.join([f'@{x.name}' for x in other_people])
                await person.send(MATCH_SCRIPT.format(list_of_ids = list_of_ids, channel_name=channel_name, invite_link=str(invite)))
                for other_person in other_people:
                    await self.send_intro(intros, person, other_person)

        self.match_in_progress = False
        await asyncio.sleep(300)
        for person in all_people:
            await person.send("It's been 5 minutes since your group started! This is your official socially acceptable time to leave :rocket:, or you can keep chatting! Type 'match me' again in #neighbourbot to start again.")


    async def get_introductions(self):
        matches = [x for x in self.guild.channels if x.name == 'introductions']
        if len(matches) == 0:
            return
        intros = {}
        channel = matches[0]
        async for message in channel.history():
            intros[message.author] = message.content
        return intros

    async def request_chat(self, message):
        await message.add_reaction(CHECKMARK)
        self.chats_requested.add(message.author)
        if self.match_in_progress:
            # just add them to the list and that's it
            return
        else:
            self.match_in_progress = True
            await self.start_match_group()

    async def announce_impending_match(self, seconds):
        num_people = len(self.chats_requested)
        neighbour_channel = await self.get_neighbour_channel()
        if num_people == 1:
            await neighbour_channel.send(f":hourglass: **{seconds} seconds!** we need more people, say 'match me' to join")
        else:
            await neighbour_channel.send(f":hourglass: **{seconds} seconds!** we have {num_people} people, say 'match me' to join")

    async def start_match_group(self):
        neighbour_channel = await self.get_neighbour_channel()
        await neighbour_channel.send(":zap: we're matching people in :hourglass: **90 seconds**! say 'match me' to join!")
        await asyncio.sleep(30)
        await self.announce_impending_match(60)
        await asyncio.sleep(30)
        await self.announce_impending_match(30)
        await asyncio.sleep(15)
        await self.announce_impending_match(15)
        await asyncio.sleep(15)
        if len(self.chats_requested) > 1:
            await neighbour_channel.send(":sparkles::sparkles::sparkles:it's happening:sparkles::sparkles::sparkles: I sent everyone a DM!")
            await self.find_chats()
        else:
            self.match_in_progress = False
            self.chats_requested.clear()
            await neighbour_channel.send("we need at least 2 people to match :frowning2: try again?")


if __name__ == '__main__':
    client = MyClient()
    client.run(os.getenv('DISCORD_TOKEN'))
