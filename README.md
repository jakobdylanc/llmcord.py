<h1 align="center">
  llmcord.py
</h1>

<p align="center">
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<h3 align="center"><i>
  Talk to LLMs with your friends!
</i></h3>

<p align="center">
  <img src="https://github.com/jakobdylanc/discord-llm-chatbot/assets/38699060/a9636e09-c89e-42e9-8690-65d52f8236ea" alt="">
</p>

## Features
- ### Elegant chat system
  Mention (@) the bot and it will reply to your message. Reply to the bot's message to continue from that point. Build conversations with reply chains!

  You can reply to any of the bot's messages to continue from wherever you want. Or reply to your friend's message (and @ the bot) to ask a question about it. There are no limits to this functionality.

  Additionally, you can seamlessly move any conversation into a [thread](https://support.discord.com/hc/en-us/articles/4403205878423-Threads-FAQ). When you @ the bot in a thread it will remember the conversation attached outside of it.

- ### Choose your LLM
  Supports models from:<br />&nbsp;&nbsp;&nbsp;- [OpenAI API](https://platform.openai.com/docs/models)<br />&nbsp;&nbsp;&nbsp;- [La plateforme de Mistral](https://mistral.ai/news/la-plateforme)

  Or run a local API server with:<br />&nbsp;&nbsp;&nbsp;- [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui)<br />&nbsp;&nbsp;&nbsp;- [LM Studio](https://lmstudio.ai)

- ### Vision support
  The bot can see image attachments when you choose a vision model.

- ### Streamed responses
  The bot's responses are dynamically generated and turn green when complete.

### And more...
- Easily set a custom personality (aka system prompt)
- DM the bot for private access (no @ required)
- User identity aware
- Fully asynchronous
- 1 Python file, ~200 lines of code

## Instructions
Before you start, install Python and clone this git repo.

1. Install Python requirements:
```bash
pip install -r requirements.txt
```

2. Create a copy of *.env.example* named *.env* and set it up:

| Setting | Instructions |
| --- | --- |
| **DISCORD_BOT_TOKEN** | Create a new Discord application at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the **Bot** tab. Also enable **MESSAGE CONTENT INTENT**. |
| **OPENAI_API_KEY** | **Only required if you choose an OpenAI API model.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL_API_KEY** | **Only required if you choose a Mistral API model.** Generate a Mistral API key at [console.mistral.ai/user/api-keys](https://console.mistral.ai/user/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|
| **LOCAL_SERVER_URL** | The URL of your local API server. **Only applicable when LLM is set to local-model.**<br />(Default: http://localhost:5000/v1) |
| **LLM** | [OpenAI API](https://platform.openai.com/docs/models):<br />&nbsp;&nbsp;&nbsp;**gpt-3.5-turbo**<br />&nbsp;&nbsp;&nbsp;**gpt-4-turbo-preview**<br />&nbsp;&nbsp;&nbsp;**gpt-4-vision-preview**<br /><br />[Mistral API](https://docs.mistral.ai/platform/endpoints):<br />&nbsp;&nbsp;&nbsp;**mistral-tiny** (Mistral-7B)<br />&nbsp;&nbsp;&nbsp;**mistral-small** (Mixtral-8X7B)<br />&nbsp;&nbsp;&nbsp;**mistral-medium** (Mistral internal prototype)<br /><br />Local API:<br />&nbsp;&nbsp;&nbsp;**local-model** |
| **CUSTOM_SYSTEM_PROMPT** | Write practically anything you want to customize the bot's behavior! |
| **ALLOWED_CHANNEL_IDS** | Discord channel IDs where the bot can send messages, separated by commas. **Leave blank to allow all channels.** |
| **ALLOWED_ROLE_IDS** | Discord role IDs that can use the bot, separated by commas. **Leave blank to allow everyone. Specifying at least one role also disables DMs.** |
| **MAX_IMAGES** | The maximum number of image attachments allowed in a single message. **Only applicable when using a vision model.**<br />(Default: 5) |
| **MAX_MESSAGES** | The maximum number of messages allowed in a reply chain.<br />(Default: 20) |

3. Invite the bot to your Discord server with this URL (replace <CLIENT_ID> with your Discord application's client ID found under the **OAuth2** tab):
```plaintext
https://discord.com/api/oauth2/authorize?client_id=<CLIENT_ID>&permissions=412317273088&scope=bot
```

4. Run the bot:
```bash
python llmcord.py
```

## Notes
- Currently only OpenAI API supports the **name** property in user messages, therefore only OpenAI API models are user identity aware (with the exception of **gpt-4-vision-preview** which also doesn't support it yet). I tried the alternate approach of prepending user's names in the message content but this didn't seem to work well with all models.

- A goal of this bot is to be compatible with all local API solutions, e.g. [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui), [LM Studio](https://lmstudio.ai), [Jan](https://jan.ai) and [ollama](https://ollama.ai/) (and maybe others I don't know about). Out of these, Jan and ollama strictly require the **model** parameter (in the chat completions request) to match the name of the model you have loaded; the other's don't care. Keeping **model** static is necessary for how this bot is coded (when **model** = local-model the code knows to point to the local API server URL). Hence why the bot only supports text-generation-webui and LM Studio for now. I'm considering [litellm](https://github.com/BerriAI/litellm) as a solution but it would still require some finesse to maintain compatibility with everything.

- I'm interested in using [chromadb](https://github.com/chroma-core/chroma) to enable asking the bot about ANYTHING in the current channel without having to reply to it. I spent time prototyping this but couldn't get to something I'm happy with.

- PRs are welcome :)

## Star History
<a href="https://star-history.com/#jakobdylanc/discord-llm-chatbot&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
  </picture>
</a>
