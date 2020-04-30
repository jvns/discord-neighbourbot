# bot.py
import os
import random

# todo: maybe make it work from a channel and not just a DM?

computer_words = [
    "binary",
    "bit",
    "broadband",
    "buffer",
    "byte",
    "capslock",
    "captcha",
    "clipart",
    "compile",
    "compress",
    "cybercrime",
    "cyberspace",
    "gigabyte",
    "hyperlink",
    "hypertext",
    "integer",
    "joystick",
"kernel",
"keyboard",
"printer",
"link",
"logic",
"macro",
"mainframe",
"memory",
"modem",
"monitor",
"motherboard",
"mouse",
"multimedia",
"network",
"offline",
"online",
"opensource",
"password",
"podcast",
"privacy",
"qwerty",
"ram",
"realtime",
"reboot",
"resolution",
"restore",
"root",
"router",
"runtime",
"save",
"scan",
"scanner",
"screen",
"screenshot",
"script",
"scrollbar",
"security",
"server",
"shareware",
"shell",
"snapshot",
"software",
"spreadsheet",
"spyware",
"statusbar",
"storage",
"supercomputer",
"surf",
"syntax",
"table",
"tag",
"teminal",
"template",
"terabyte",
"thread",
"toolbar",
"trash",
"typeface",
"undo",
"unix",
"upload",
"url",
"username",
"utility",
"version",
"virtual",
"virus",
"web",
"webhost",
"webmaster",
"website",
"widget",
"wiki",
"windows",
"wireless",
"workstation",
"worm",
"www",
"xml",
"zip",
]

flower_words = [
"acacia",
"acanthus",
"aloe",
"amaranth",
"american ash",
"angelica",
"anthericum",
"arum",
"aspen",
"barberry",
"basil",
"bellflower",
"blackthorn",
"bluebottle",
"borage",
"bramble",
"bryony",
"bugloss",
"burdock",
"cactus",
"cinquefoil",
"clianthus",
"coltsfoot",
"coriander",
"crowfoot",
"dahlia",
"daffodil",
"daisy",
"dandelion",
"date",
"daylily",
"dittany",
"dock",
"dodder",
"dragonplant",
"fennel",
"fieldrush",
"foxglove",
"geranium",
"gilliflower",
"goosefoot",
"hazel",
"hedysarum",
"heath",
"helenium",
"hepatica",
"hibiscus",
"hogbean",
"holly",
"hollyhock",
"honeysuckle",
"hornbeam",
"hortensia",
"hyacinth",
"iris",
"ivy",
"jessamine",
"kalmia",
"laburnum",
"larch",
"larkspur",
"laurel",
"laurestine",
"lavender",
"lichen",
"lilac",
"lily",
"lucerne",
"madder",
"manchineel",
"mandrake",
"marigold",
"marshmallow",
"meadowsweet",
"mezereon",
"milfoil",
"milkwort",
"mistletoe",
"motherwort",
"mugwort",
"myrtle",
"narcissus",
"nettle",
"nightshade",
"nosegay",
"ophrys",
"orangeblossom",
"osmunda",
"pansy",
"parsley",
"peony",
"peppermint",
"periwinkle",
"polemonium",
"pomegranate",
"pricklypear",
"primrose",
"privet",
"quesnelia",
"quince",
"reed",
"restharrow",
"rose",
"rosemary",
"saffron",
"sage",
"silverweed",
"snowball",
"snowdrop",
"southernwood",
"speedwell",
"starwort",
"succory",
"sunflower",
"syringa",
"tares",
"teasel",
"thyme",
"toadflax",
"touch-me-not",
"tuberose",
"tulip",
"turnsol",
"umbrellaplant",
"valerian",
"vervain",
"violet",
"wallflower",
"waterlily",
"willowherb, purple",
"woad",
"wormwood",
"yew",
"yellowroot",
"yucca",
"zephyranthes",
        ]
import discord
import asyncio
TOKEN = os.getenv('DISCORD_TOKEN')

MESSAGE_OVER_SCRIPT="""
It’s been 5 minutes! this is your official time to end the conversation if you'd like :)!
Press 💬 to have another chat!
Or you can get some tea, or keep talking to the same people if you’d like!
"""

MATCH_SCRIPT="""
Your neighbour is @{username}! Join voice chat #{channel_name} with them:
⏩  {invite_link} ⏪
"""

HELP_MESSAGE = """
Hi! I can connect you with 2 other !!Con attendees for a 5 minute chat!

This is like chatting with the people in the seats next to you when you’re watching a talk :). How it works:

1. Get matched!
2. Join the voice channel I give you with your 2 neighbours!
3. After 5 minutes, I'll send you a message and you can request another chat!

Press 💬 under this message to request a chat!
"""

EMOJI_ANOTHER_CHAT = '💬'

NEIGHBOUR_CATEGORY='Chat with neighbours!'
def random_channel_name():
    return random.choice(computer_words) + '-' + random.choice(flower_words)

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        self.chats_requested = dict() # maps users to the channel the message was on
        await self.find_chats()

    def get_neighbour_category(self):
        # todo: maybe add error handling lol
        return [x for x in self.guilds[0].categories if x.name == NEIGHBOUR_CATEGORY][0]

    async def create_and_invite_voice_channel(self):
        category = self.get_neighbour_category()
        channel_name = random_channel_name()
        channel = await category.create_voice_channel(channel_name)
        invite = await channel.create_invite()
        return invite, channel_name

    async def find_chats(self):
        while True:
            if len(self.chats_requested) >= 2:
                person_1, person_2 = list(self.chats_requested.keys())[:2]
                channel_1 = self.chats_requested.pop(person_1)
                channel_2 = self.chats_requested.pop(person_2)
                invite, channel_name = await self.create_and_invite_voice_channel()
                invite = str(invite)
                message_1 = await channel_1.send(MATCH_SCRIPT.format(username=str(person_2), channel_name=channel_name, invite_link=invite))
                message_2 = await channel_2.send(MATCH_SCRIPT.format(username=str(person_1), channel_name=channel_name, invite_link=invite))
                await asyncio.sleep(300)
                message = await channel_1.send(MESSAGE_OVER_SCRIPT)
                await message.add_reaction(EMOJI_ANOTHER_CHAT)
                message = await channel_2.send(MESSAGE_OVER_SCRIPT)
                await message.add_reaction(EMOJI_ANOTHER_CHAT)
            else:
                print("oh no nothing yet", len(self.chats_requested))
                # hang out for 5 seconds and try again later
                await asyncio.sleep(5)

    async def request_chat(self, message):
        await message.channel.send("Yay! I'm requesting a chat for you!")
        person = message.channel.recipient
        self.chats_requested[str(person)] = message.channel

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return
        if reaction.emoji == EMOJI_ANOTHER_CHAT :
            await self.request_chat(reaction.message)

    async def on_message(self, message):
        if type(message.channel) != discord.DMChannel:
            # ignore anything that isn't a DM
            return
        elif message.author == self.user:
            # ignore messages from the bot
            return
        elif message.content.lower().startswith('hi'):
            sent = await message.channel.send(HELP_MESSAGE)
            await sent.add_reaction(EMOJI_ANOTHER_CHAT)
        elif message.content.lower().startswith('help'):
            sent = await message.channel.send(HELP_MESSAGE)
            await sent.add_reaction(EMOJI_ANOTHER_CHAT)
        elif message.content.startswith('!5minchat'):
            await self.request_chat(message)
        else:
            await message.channel.send("I didn't understand that! Type 'help' to get help.")

if __name__ == '__main__':
    client = MyClient()
    client.run(TOKEN)
