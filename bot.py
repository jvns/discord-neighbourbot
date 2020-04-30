# bot.py
import os
import random
import asyncio
from datetime import datetime, timezone, timedelta
import discord
import asyncio
TOKEN = os.getenv('DISCORD_TOKEN')

MATCH_SCRIPT="""
<@{id1}> and <@{id2}> are neighbours! Go chat in **#{channel_name}** {invite_link} !
"""
CHECKMARK='☑️'
NEIGHBOUR_CATEGORY='Chat with neighbours!'

def read_words(filename):
    with open(filename) as f:
        return [x.strip() for x in f.readlines()]

computer_words = read_words('computer.txt')
flower_words = read_words('flowers.txt')

def random_channel_name():
    return random.choice(computer_words) + '-' + random.choice(flower_words)

class MyClient(discord.Client):
    def __init__(self):
        self.chats_requested = dict() # maps users to the channel the message was on
        super().__init__()

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        # delete old channels in the background
        await asyncio.gather(self.find_chats(), self.delete_old_channels())

    def get_neighbour_category(self):
        # todo: maybe add error handling lol
        return [x for x in self.guilds[0].categories if x.name == NEIGHBOUR_CATEGORY][0]

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
        while True:
            if len(self.chats_requested) >= 2:
                person_1, person_2 = list(self.chats_requested.keys())[:2]
                channel_1 = self.chats_requested.pop(person_1)
                invite, channel_name = await self.create_and_invite_voice_channel()
                message_1 = await channel_1.send(MATCH_SCRIPT.format(id1=person_1.id, id2=person_2.id, channel_name=channel_name, invite_link=str(invite)))
            else:
                print("oh no nothing yet", len(self.chats_requested))
                # hang out for 5 seconds and try again later
                await asyncio.sleep(5)

    async def request_chat(self, message):
        await message.add_reaction(CHECKMARK)
        person = message.author
        self.chats_requested[person] = message.channel

    async def on_message(self, message):
        if message.channel.name != 'neighbourbot':
            # ignore anything that isn't a DM
            return
        elif message.author == self.user:
            # ignore messages from the bot
            return
        elif message.content.lower().startswith('match me'):
            await self.request_chat(message)

if __name__ == '__main__':
    client = MyClient()
    client.run(TOKEN)
