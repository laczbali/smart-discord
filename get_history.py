# This script can be used to download chat history,
# so that the data can be used for training a custom model

import discord
import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
GUILD_NAME = "" # Name of the guild, which you want to download
MESSAGE_LIMIT_PER_CHANNE = 500 # Number of messages to download per channel
REPLACE_NAME = "" # name of a user, which you want to train the bot to respond as
BOT_NAME = os.environ.get('BOT_NAME')
# -----------------------------------------------------------------------------

# set up discord client
client = discord.Client()

# on login
@client.event
async def on_ready():
    print("bot ready")

    # get guild by name
    guild = discord.utils.get(client.guilds, name=GUILD_NAME)

    # get all channels
    all_messages = []

    for channel in guild.text_channels:
        print(channel.name)

        # get all messages
        history = await channel.history(limit=MESSAGE_LIMIT_PER_CHANNE).flatten()
        history.reverse()

        ch_messages = []

        for m in history:
            content = m.content

            # replace mention IDs with names
            for mention in m.mentions:
                content = content.replace(f"<@!{mention.id}>", mention.name)

            # format message
            out = f"{m.author.name}: {content}"

            # replace the name of a user with the name of the bot
            # so that the prompts later are lined up with the training data
            if REPLACE_NAME != "":
                out = out.replace(REPLACE_NAME, BOT_NAME)

            # return
            ch_messages.append(out)

        # save channel messages to file
        with open(f"{channel.name}.history.txt", "w", encoding="utf-8") as f:
            for m in ch_messages:
                f.write(f"{m}\n")

        all_messages.extend(ch_messages)

    # save all messages to file
    with open("all.history.txt", "w", encoding="utf-8") as f:
        for m in all_messages:
            f.write(f"{m}\n")

    print("done")

    

# start the bot
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
client.run(DISCORD_TOKEN)