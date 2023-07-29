# gpt_discord by jakobdylanc
The purest OpenAI GPT Discord bot.

# Features
### INTUITIVE REPLY-BASED CHAT SYSTEM
To start a new conversation, @ the bot. To continue a conversation, reply to the message. The conversation context is based on the Discord message reply chain.
Works in DMs too, no @ necessary.

### STREAMED RESPONSES
The bot's replies generate gradually rather than having to wait for it to send in one big chunk.
>As of writing this no other OpenAI GPT Discord bot has successfully implemented this. Feel free to prove me wrong :)

### ULTRA REFINED
1 Python file, 100 lines of code.

![](https://github.com/jakobdylanc/gpt_discord/assets/38699060/e496bb18-616a-40ac-93f4-42fe09488747)

# Instructions
1. Install Python requirements:
```bash
pip install -r requirements.txt
```

2. Create _.env_ from _.env.example_ and set it up:

| Option | Instructions |
| --- | --- |
| DISCORD\_BOT_TOKEN | Create a new Discord application at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the "Bot" tab. Also enable "message content intent". |
| OPENAI\_API_KEY | Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| GPT_MODEL | Choose between "gpt-4", "gpt-4-32k", "gpt-3.5-turbo", or "gpt-3.5-turbo-16k". Make sure your OpenAI account has access to the model you choose. |
| CUSTOM\_SYSTEM_PROMPT | Write practically anything you want to customize the bot's behavior! |

3. Invite the bot to your Discord server with this URL (replace <CLIENT_ID> with your Discord application's client ID found under the "OAuth2" tab):
```plaintext
https://discord.com/api/oauth2/authorize?client_id=<CLIENT_ID>&permissions=412317273088&scope=bot
```

4. Run the bot:
```bash
python gpt_discord.py
```
