# smart-discord
A Discord bot that will reply on occasion to convesations.

It can be configured how often it replies, with the MAX_CHANCE, MIN_CHANCE and THRESHOLD values.
- With every message sent, to any channel, there is a MIN_CHANCE value that the bot will reply
- As more and more time pass since the last time the bot replied, the chance will rise
- The chance will reach the MAX_CHANCE value, once the last the the bot replied was THRESHOLD hours ago
- The bot will reply every time it is @mentioned.

When it replies, it will take the last CONTEXT_COUNT messages in the channel as a context to its reply.

You can't invite a ready-made version of this. You need to set up your own.

Powered by [OpenAI](https://openai.com/)

# Setup
## Discord
1. Go to [Discord dev site](https://discord.com/developers/applications)
2. New application
3. Bot \ Add Bot
   - Set public status
   - OAuth is not needed 
4. Go to OAuth2 \ URL Generator
5. Select the `bot` scope
6. Select the following permissions:
    - Read messages/view channels
    - Send messages
    - Send messages in threads
    - Read message history
7. Use the generated URL to invite the bot


## Python
1. Install requirements `pip install -r .\requirements.txt`
2. Create a blank `.env` file in the root directory
3. Add the Discord Secret Token to the `.env` file
    - `DISCORD_TOKEN=YOUR_KEY_HERE`
4. Set the OpenAI .env variables
   - `OPENAI_TOKEN=YOUR_KEY_HERE`
   - `PROMPT_PREFIX=THIS_WILL_BE_ADDED_TO_THE_MESSAGE_CONTEXT`
   - `BOT_NAME=THE_NAME_YOU_GAVE_TO_THE_BOT_IN_STEP3`
5. Run main.py
