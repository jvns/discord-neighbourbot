# discord-neighbourbot

a little discord bot to match you with random people to chat with

### running on heroku

You should be able to set up this bot on a free Heroku account pretty easily --
the repository comes with a `Procfile` and requirements already set up to run
on Heroku. This [medium
article](https://medium.com/@mason.spr/hosting-a-discord-js-bot-for-free-using-heroku-564c3da2d23f)
has pretty good instructions.

### running locally

```
virtualenv vendor -p /usr/bin/python3
source vendor/bin/activate
pip install -r requirements.txt
env DISCORD_TOKEN=YOUR_TOKEN ./vendor/bin/python3 bot.py
```

### problems with the bot

the biggest problem we had when using the bot in practice was that the window
when people can be matched is really short (1 minute). It turns out that it's
hard to make sure that everyone is actually there during that 1 minute window,
so we sometimes had sad interactions like:

```
person: match me
... a minute passes ...
bot: we need at least 2 people to match :frowning2: try again?
```

Maybe there is a way to make this better! I'd love to hear what you come up
with! (julia@jvns.ca)
