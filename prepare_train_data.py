# this script turns a logfile created with get_history.py
# and turns it into a JSONL file that can be used for training
# 
# that script should be set up in a way, that one of the guild users names
# gets replaced with the name of your bot,
# since the prompts will use the bot's name

# required output is
# {"prompt": "..", "completion": "..."}
# {"prompt": "..", "completion": "..."}
# ...

# structure of this script:
# - read the log message-by-message
# - if a message is from a normal user, append it to the current prompt
# - if a message is from the "bot", append it to the current completion
# - on a bot->user change, write the current prompt and completion to the JSONL file


import json
import os
from dotenv import load_dotenv

load_dotenv()
BOT_NAME = os.environ.get('BOT_NAME')

# read the json log file
with open("all.history.json") as f:
    log = json.load(f)

# parse log
current_prompt = ""
current_completion = ""
last_message_source = ""
for entry in log:
    name = entry[0]
    message = entry[1]

    # if the message is from a user, append it to the current prompt
    if name != BOT_NAME:
        if last_message_source == 'bot':
            # previous message was from the bot,
            # so this is the beginning of a new prompt
            # we need to write the previous prompt and completion to the JSONL file
            current_prompt = current_prompt.strip()
            current_prompt = f"{current_prompt}\n{BOT_NAME}:"
            current_completion = current_completion.strip()

            if current_completion != "":
                # create a new entry only if the completion is not empty
                current_completion = f" {current_completion}"

                out = {"prompt": current_prompt, "completion": current_completion}
                with open("train.jsonl", "a") as f:
                    f.write(json.dumps(out) + "\n")

            # reset the current prompt and completion
            current_prompt = ""
            current_completion = ""
            last_message_source = ""

        last_message_source = "user"
        current_prompt += f"{name}: {message}\n"

    # if the message is from the bot, append it to the current completion
    if name == BOT_NAME:
        last_message_source = "bot"
        current_completion += message + "\n"