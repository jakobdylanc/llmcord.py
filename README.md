<h1 align="center">
  llmcord<br>
  (by jakobdylanc)
</h1>

<p align="center">
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<p align="center">
  <img src="https://github.com/jakobdylanc/llmcord/assets/38699060/46706bfc-6688-4e58-8a23-c5bed8c9b2b1" alt="">
</p>

# Features
- ### BEST CHAT SYSTEM
  @ the bot and it will reply to your message. Reply to the bot's message to continue the conversation from that point. Build conversations with reply chains!
  > Works when replying to ANY message in your server, just @ the bot!

- ### STREAMED RESPONSES
  The bot's responses are dynamically generated just like ChatGPT.
  > With intuitive color coding (orange = generating, green = done).

- ### VISION SUPPORT
  The bot can see your image attachments when set to a vision model.

### And more...
- Choose OpenAI or Mistral API
- Easily set a custom personality
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
| **DISCORD\_BOT_TOKEN** | Create a new Discord application at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the **Bot** tab. Also enable **MESSAGE CONTENT INTENT**. |
| **OPENAI\_API_KEY** | **Only required if you select an OpenAI model.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL\_API_KEY** | **Only required if you select a Mistral model.** Generate a Mistral API key at [console.mistral.ai/user/api-keys](https://console.mistral.ai/user/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|
| **LLM** | [OpenAI models](https://platform.openai.com/docs/models):<br />&nbsp;&nbsp;&nbsp;**gpt-3.5-turbo-1106** (latest GPT-3.5 Turbo)<br />&nbsp;&nbsp;&nbsp;**gpt-4-1106-preview** (GPT-4 Turbo)<br />&nbsp;&nbsp;&nbsp;**gpt-4-vision-preview** (GPT-4 Turbo with vision)<br />[Mistral models](https://docs.mistral.ai/platform/endpoints):<br />&nbsp;&nbsp;&nbsp;**mistral-tiny** (Mistral-7B)<br />&nbsp;&nbsp;&nbsp;**mistral-small** (Mixtral-8X7B)<br />&nbsp;&nbsp;&nbsp;**mistral-medium** (Mistral internal prototype) |
| **MAX_IMAGES** | The maximum number of image attachments allowed in a single message. Only applicable when using a vision model. (Default: 5) |
| **MAX_MESSAGES** | The maximum number of messages in a reply chain. (Default: 20) |
| **CUSTOM\_SYSTEM_PROMPT** | Write practically anything you want to customize the bot's behavior! |

3. Invite the bot to your Discord server with this URL (replace <CLIENT_ID> with your Discord application's client ID found under the ***OAuth2*** tab):
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
