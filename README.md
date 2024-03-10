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
- ### Collaborative prompting
  @ the bot and it will reply to your message. Reply to the bot's message to continue from that point. Build conversations with reply chains!
 
  You can reply to any of the bot's messages to continue from any point. Or reply to your friend's message and @ the bot to ask a question about it. There are no limits to this functionality.

  Additionally:
  - Back-to-back messages from the same user are automatically chained together. Just reply to the latest one and the bot will see all of them.
  - You can seamlessly move any conversation into a [thread](https://support.discord.com/hc/en-us/articles/4403205878423-Threads-FAQ). Just create a thread from any message and @ the bot inside to continue.

- ### Choose your LLM
  Supports models from [OpenAI API](https://platform.openai.com/docs/models), [Mistral API](https://mistral.ai/news/la-plateforme), [ollama](https://github.com/ollama/ollama) and many more thanks to [LiteLLM](https://github.com/BerriAI/litellm).

  Also supports:
  - [oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui)
  - [Jan](https://jan.ai)
  - [LM Studio](https://lmstudio.ai)
  - Any other OpenAI compatible options should work too

- ### Vision support
  The bot can see image attachments when you choose a vision model.

- ### Streamed responses
  The bot's responses are dynamically generated and turn green when complete.

### And more...
- Easily set a custom personality
- DM the bot for private access (no @ required)
- User identity aware
- Fully asynchronous
- 1 Python file, ~200 lines of code

## Instructions
Before you start, install Python and clone this git repo.

1. Install Python requirements: `pip install -r requirements.txt`

2. Create a copy of *.env.example* named *.env* and set it up (see below)

3. Run the bot: `python llmcord.py`

| Setting | Instructions |
| --- | --- |
| **DISCORD_BOT_TOKEN** | Create a new Discord bot at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the **Bot** tab. Also enable **MESSAGE CONTENT INTENT**. |
| **DISCORD_CLIENT_ID** | Found under the **OAuth2** tab of the Discord bot you just made. |
| **LLM** | For [LiteLLM supported providers](https://github.com/BerriAI/litellm?tab=readme-ov-file#supported-providers-docs) ([OpenAI API](https://docs.litellm.ai/docs/providers/openai), [Mistral API](https://docs.litellm.ai/docs/providers/mistral), [ollama](https://docs.litellm.ai/docs/providers/ollama), etc.), follow the LiteLLM instructions for its model name formatting.<br /><br />For [Jan](https://jan.ai), set to **`local/openai/<MODEL_NAME>`** where **<MODEL_NAME>** is the name of the model you have loaded.<br /><br />For [oobabooga](https://github.com/oobabooga/text-generation-webui) and [LM Studio](https://lmstudio.ai), set to **`local/openai/model`** regardless of the model you have loaded. |
| **LLM_MAX_TOKENS** | The maximum number of tokens in the LLM's chat completion.<br />(Default: `1024`) |
| **LLM_TEMPERATURE** | LLM sampling temperature value. Higher values make the LLM's output more random.<br />(Default: `1.0`) |
| **LLM_TOP_P** | LLM nucleus sampling value. **Alternative to sampling temperature.** Higher values make the LLM's output more diverse.<br />(Default: `1.0`) |
| **CUSTOM_SYSTEM_PROMPT** | Write practically anything you want to customize the bot's behavior! |
| **CUSTOM_DISCORD_STATUS** | Set a custom message that displays on the bot's Discord profile. **Max 128 characters.** |
| **ALLOWED_CHANNEL_IDS** | Discord channel IDs where the bot can send messages, separated by commas. **Leave blank to allow all channels.** |
| **ALLOWED_ROLE_IDS** | Discord role IDs that can use the bot, separated by commas. **Leave blank to allow everyone. Specifying at least one role also disables DMs.** |
| **MAX_IMAGES** | The maximum number of image attachments allowed in a single message. **Only applicable when using a vision model.**<br />(Default: `5`) |
| **MAX_MESSAGES** | The maximum number of messages allowed in a reply chain.<br />(Default: `20`) |
| **LOCAL_SERVER_URL** | The URL of your local API server. **Only applicable when LLM starts with `local/`.**<br />(Default: `http://localhost:5000/v1`) |
| **LOCAL_API_KEY** | The API key to use with your local API server. **Only applicable when LLM starts with `local/`. Usually safe to leave blank.** |
| **OOBABOOGA_CHARACTER** | Your [oobabooga character](https://github.com/oobabooga/text-generation-webui/wiki/03-%E2%80%90-Parameters-Tab#character) that you want to use. **Only applicable when using oobabooga. Leave blank to use CUSTOM_SYSTEM_PROMPT instead.** |
| **OPENAI_API_KEY** | **Only required if you choose an OpenAI API model.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL_API_KEY** | **Only required if you choose a Mistral API model.** Generate a Mistral API key at [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|

> **OPENAI_API_KEY** and **MISTRAL_API_KEY** are provided as examples. Add more as needed for other [LiteLLM providers](https://docs.litellm.ai/docs/providers).

## Notes
- Vision support is currently limited to **gpt-4-vision-preview** from OpenAI API. Support for local vision models like llava is planned.

- Only models from OpenAI API are user identity aware (excluding **gpt-4-vision-preview** for now). This is because only OpenAI API supports the **name** property in the user message object. I tried the alternate approach of prepending user's names in the message body but this doesn't seem to work well with all models.

- PRs are welcome :)

## Star History
<a href="https://star-history.com/#jakobdylanc/discord-llm-chatbot&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
  </picture>
</a>
