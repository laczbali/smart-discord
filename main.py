import datetime
import json
import os
import random
from dotenv import load_dotenv
import discord
import openai

from numpy import interp


# load discord client
client = discord.Client()

# --------------------------------------------------

def get_or_create_fileconst(key, defaultvalue):
    """
    Returns the value of the key in the fileconst.json file, or creates it if it doesn't exist
    """

    # create file if missing, with the current key:defaultvalue in it & return the default value
    fileconst_path = os.path.join(os.path.dirname(__file__), 'fileconst.json')
    if not os.path.exists(fileconst_path):
        with open(fileconst_path, 'w') as f:
            f.write(json.dumps({key: defaultvalue}))

        return defaultvalue

    # read the file
    with open(fileconst_path, 'r') as f:
        fileconst = json.loads(f.read())
    
    # if the key is missing, create it with the default value
    if key not in fileconst:
        fileconst[key] = defaultvalue
        with open(fileconst_path, 'w') as f:
            f.write(json.dumps(fileconst))

    # return the value of the key if found, or the defaultvalue if not
    return fileconst[key]


def set_fileconst(key, value):
    """
    Set a new value for a fileconst key (so that it can be changed remotely)
    """

    fileconst_path = os.path.join(os.path.dirname(__file__), 'fileconst.json')

    # create the file with the key:value pair if the file doesn't exist
    if not os.path.exists(fileconst_path):
        with open(fileconst_path, 'w') as f:
            f.write(json.dumps({key: value}))
        return

    # read the file
    with open(fileconst_path, 'r') as f:
        fileconst = json.loads(f.read())
    
    # update the key
    fileconst[key] = value

    # write the file
    with open(fileconst_path, 'w') as f:
        f.write(json.dumps(fileconst))


async def hours_since_posted(guide_id):
    """
    Returns how many hours have passed since the last post by the bot
    """

    # get guild
    guild = client.get_guild(guide_id)

    # get all channels in guild
    channels = guild.channels

    # get the last message posted by the bot
    last_message = None
    for ch in channels:
        # skip channel if it has no history attribute
        if not hasattr(ch, 'history'):
            continue
    
        history = await ch.history(limit=500).flatten()
        for msg in history:
            # break, if we found the last message by the bot in this channel
            if msg.author.id == client.user.id:
                #  update the last_message if the message is newer
                if last_message is None or msg.created_at > last_message.created_at:
                    last_message = msg
                break

    # if there is no last message, return infinity
    if last_message is None:
        return float('inf')

    # get the time difference between now and the last message, in hours
    message_created_utc = last_message.created_at
    now_utc = datetime.datetime.utcnow()
    delta = now_utc - message_created_utc
    hours = delta.total_seconds() / 3600
    return hours


def should_reply(mentioned, posted_since_h) -> bool:
    # always reply if the bot was mentioned
    if mentioned:
        return True

    # the bot should post roughly once per THRESHOLD hours
    # if it posted more than THRESHOLD hours ago, it should reply with MAX_CHANCE
    # if it posted 0 hours ago, it should reply with MIN_CHANCE
    # between those two, the chance is a linear function
    THRESHOLD = get_or_create_fileconst('THRESHOLD', 10)
    MIN_CHANCE = get_or_create_fileconst('MIN_CHANCE', 0.05)
    MAX_CHANCE = get_or_create_fileconst('MAX_CHANCE', 0.95)
    
    chance = interp(posted_since_h, [0, THRESHOLD], [MIN_CHANCE, MAX_CHANCE])

    # if the chance is greater than a random number between 0 and 1, reply
    random_num = random.random()
    print(f'chance: {chance}, random_num: {random_num}, result: {chance > random_num}')
    return chance > random_num


async def get_context(channel):
    """
    Gets the last N messages in the channel, and returns them in a single string, formatted like this:
    
    user1: message1
    user2: message2
    user1: message3
    user1: message4
    user3: message5
    """
    
    # get the last N messages in the channel
    CONTEXT_COUNT = int(get_or_create_fileconst('CONTEXT_COUNT', 5))
    history = await channel.history(limit=CONTEXT_COUNT).flatten()
    history.reverse()

    # build response
    msg = ''
    for m in history:
        content = m.content

        for mention in m.mentions:
            content = content.replace(f"<@!{mention.id}>", mention.name)

        msg += f'{m.author.name}: {content}\n'

    return msg.strip()



def query_openai(context):
    """
    Build and sends a completion query to OpenAI.
    The prompt will be:

    PREFIX\n
    CONTEXT\n
    BOTNAME:

    The response will be the first non-whitespace line of the API response.
    """
    try:
        # bulid the prompt
        PREFIX = os.environ.get('PROMPT_PREFIX')
        BOTNAME = os.environ.get('BOT_NAME')
        prompt = f"{PREFIX}\n\n{context}\n{BOTNAME}:"

        print(f"----------\nSending prompt:\n\n{prompt}\n----------")
        
        # send the request
        openai.api_key = os.getenv("OPENAI_TOKEN")
        response = openai.Completion.create(
            engine="text-davinci-001",
            prompt=prompt,
            temperature=0.9,
            max_tokens=64,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=[":"]
        )

        # return the first non-whitespace line of the response
        return response.choices[0].text.strip().split('\n')[0]

    except Exception as e:
        print(str(e))
        return "¯\_(ツ)_/¯"

# --------------------------------------------------

# say hello on bot-login
@client.event
async def on_ready():
    print('bot ready')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for /help"))


# handlle messages on server
@client.event
async def on_message(message):
    # ignore messages from self
    if message.author == client.user:
        return

    # ignore messages from bots
    if message.author.bot:
        return

    # post help, if requested
    if (client.user in message.mentions) and ("/help" in message.content):
        MIN_CHANCE = get_or_create_fileconst('MIN_CHANCE', 0.05)
        MAX_CHANCE = get_or_create_fileconst('MAX_CHANCE', 0.95)
        THRESHOLD = get_or_create_fileconst('THRESHOLD', 10)
        CONTEXT_COUNT = get_or_create_fileconst('CONTEXT_COUNT', 5)

        await message.channel.send(
        "**Hi! I'm a bot that is powered by OpenAI!** \n" +

        "I will respond to each message that I'm @mentioned in. \n" +
        "Otherwise I will respond every now and then. \n" +

        "\n" +

        f"If it has been **more than {THRESHOLD} hours** since I've posted, I will reply with **{MAX_CHANCE*100}% chance.** \n" +
        f"If it has been **0 hours**, I will reply with **{MIN_CHANCE*100}% chance.** \n" +
        f"Between those two, I will reply with a linear function of the hours passed. \n" +
        f"I check the **last {CONTEXT_COUNT} messages** for context, when I reply. \n" +

        "\n" +

        "To change the chances, the hours or how much context I should look at, use the following command: \n" +
        "`@mr.gazsi /set MIN_CHANCE|MAX_CHANCE|THRESHOLD|CONTEXT_COUNT VALUE` \n" +
        "The VALUE is a number between 0 and 1 for the chances and an integer for the threshold hours and the context \n" +
        "- `@mr.gazsi /set MIN_CHANCE 0.05` \n" +
        "- `@mr.gazsi /set MAX_CHANCE 0.95` \n" +
        "- `@mr.gazsi /set THRESHOLD 10` \n" +
        "- `@mr.gazsi /set CONTEXT_COUNT 5` \n" +

        "\n" +
        
        "made by **blaczko#0134** - <https://github.com/laczbali/smart-discord> \n" +
        "Powered by - <https://openai.com/>"
        )
        return

    # respond to value update requests
    if (client.user in message.mentions) and ("/set" in message.content):
        try:
            # split the message into words
            content = message.content.split('/set')[1].strip()
            words = content.split(' ')
            # get the key and value
            key = words[0]
            value = words[1]

            if key not in ['MIN_CHANCE', 'MAX_CHANCE', 'THRESHOLD', 'CONTEXT_COUNT']:
                raise ValueError
            
            if key in ['MIN_CHANCE', 'MAX_CHANCE']:
                if float(value) < 0 or float(value) > 1:
                    raise ValueError

            if key in ['THRESHOLD', 'CONTEXT_COUNT']:
                if int(value) < 0:
                    raise ValueError

            # set the key:value pair
            set_fileconst(key, float(value))
            # reply
            await message.channel.send(f"**{key}** set to `{value}`")
        except:
            await message.channel.send("invalid command, see `@mr.gazsi /help`")
        return

    # get guild id from message
    guild_id = message.guild.id

    # get if the bot was mentioned
    mentioned = (client.user in message.mentions)

    # get the last time the bot posted in this guild
    posted_since_h = await hours_since_posted(guild_id)

    # determine if the bot should post
    do_reply = should_reply(mentioned, posted_since_h)

    if do_reply:
        # get the context
        context = await get_context(message.channel)

        # query openai
        query = query_openai(context)

        # post the response
        await message.channel.send(query)

# --------------------------------------------------

# read token from .env
load_dotenv()
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

# run client
client.run(DISCORD_TOKEN)