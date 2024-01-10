<h1 align="center">
  llmcord<br>
  A Discord AI chat bot<br>
  (by jakobdylanc)
</h1>

<p align="center">
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<h3 align="center"><i>
  Talk to LLMs with your friends!
</i></h3>

<p align="center">
  <img src="https://github.com/jakobdylanc/llmcord/assets/38699060/fb6c75c4-f972-452e-a197-e70afd6e7d0c" alt="">
</p>

# Features
- ### Elegant chat system
  @ the bot and it will reply to your message. Anyone can reply to the bot's message to continue from that point. The message reply chain is the conversation thread.
  > Works when replying to ANY message in your server, just @ the bot!
 
- ### Choose your LLM
  llmcord is cross-compatible with [OpenAI API](https://platform.openai.com/docs/models), [Mistral's La platforme](https://docs.mistral.ai/platform/endpoints), and local models with [LM Studio](https://lmstudio.ai).

- ### Streamed responses
  The bot's responses are dynamically generated just like ChatGPT.
  > When the message turns green, it's done.

- ### Vision support
  The bot can see your image attachments when you choose a vision model.

### And more...
- Easily set a custom personality (aka system prompt)
- User identity aware
- Fully asynchronous
- 1 Python file, ~200 lines of code

# Instructions
> Before you start, install Python and clone this git repo.
1. Install Python requirements:
```bash
pip install -r requirements.txt
```

2. Create _.env_ from _.env.example_ and set it up:

| Setting | Instructions |
| --- | --- |
| **DISCORD_BOT_TOKEN** | Create a new Discord application at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the **Bot** tab. Also enable **MESSAGE CONTENT INTENT**. |
| **OPENAI_API_KEY** | **Only required if you choose an OpenAI API model.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL_API_KEY** | **Only required if you choose a Mistral API model.** Generate a Mistral API key at [console.mistral.ai/user/api-keys](https://console.mistral.ai/user/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|
| **LM_STUDIO_URL** | **Only required if you choose to run a local model with LM Studio's local inference server.**<br />(Default: http://localhost:1234/v1) |
| **LLM** | [OpenAI API models](https://platform.openai.com/docs/models):<br />&nbsp;&nbsp;&nbsp;**gpt-3.5-turbo-1106** (latest GPT-3.5 Turbo)<br />&nbsp;&nbsp;&nbsp;**gpt-4-1106-preview** (GPT-4 Turbo)<br />&nbsp;&nbsp;&nbsp;**gpt-4-vision-preview** (GPT-4 Turbo with vision)<br /><br />[Mistral API models](https://docs.mistral.ai/platform/endpoints):<br />&nbsp;&nbsp;&nbsp;**mistral-tiny** (Mistral-7B)<br />&nbsp;&nbsp;&nbsp;**mistral-small** (Mixtral-8X7B)<br />&nbsp;&nbsp;&nbsp;**mistral-medium** (Mistral internal prototype)<br /><br />[LM Studio](https://lmstudio.ai) (locally running model):<br />&nbsp;&nbsp;&nbsp;**local-model** |
| **CUSTOM_SYSTEM_PROMPT** | Write practically anything you want to customize the bot's behavior! |
| **ALLOWED_ROLE_IDS** | Discord role IDs that can use the bot, separated by commas. **Leave blank to allow everyone.**<br /><br />When left blank, the bot also allows DMs from mutual server members. |
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

# Star History
<a href="https://star-history.com/#jakobdylanc/llmcord&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/llmcord&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/llmcord&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jakobdylanc/llmcord&type=Date" />
  </picture>
</a>
