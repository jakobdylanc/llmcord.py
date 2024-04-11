<h1 align="center">
  llmcord.py
</h1>

<h3 align="center"><i>
  Talk to LLMs with your friends!
</i></h3>

<p align="center">
  <img src="https://github.com/jakobdylanc/discord-llm-chatbot/assets/38699060/789d49fe-ef5c-470e-b60e-48ac03057443" alt="">
</p>

llmcord.py is ~200 lines of Python code that enables collaborative multi-turn LLM prompting in your Discord server. It uses message reply chains to build conversations. Just @ the bot to start a conversation and reply to continue.

You can reply to ANY of the bot's messages to continue ANY conversation from ANY point. Or @ the bot while replying to your friend's message to ask a question about it. There are no limits to this functionality.

Additionally:
- Back-to-back messages from the same user are automatically chained together. Just reply to the latest one and the bot will see all of them.
- You can seamlessly move any conversation into a [thread](https://support.discord.com/hc/en-us/articles/4403205878423-Threads-FAQ). Just create a thread from any message and @ the bot inside to continue.

Supports remote models from [OpenAI API](https://platform.openai.com/docs/models), [Mistral API](https://docs.mistral.ai/platform/endpoints), [Anthropic API](https://docs.anthropic.com/claude/docs/models-overview) and many more thanks to [LiteLLM](https://github.com/BerriAI/litellm).

Or run a local model with [ollama](https://ollama.com), [oobabooga](https://github.com/oobabooga/text-generation-webui), [Jan](https://jan.ai), [LM Studio](https://lmstudio.ai) or any other OpenAI compatible API server.

And more:
- Supports image attachments when using a vision model
- Customizable system prompt
- DM for private access (no @ required)
- User identity aware (OpenAI API only)
- Streamed responses (turns green when complete, automatically splits into separate messages when too long, throttled to prevent Discord ratelimiting)
- Automatically displays helpful user warnings when appropriate (like "Only using last 20 messages", "Max 5 images per message", etc.)
- Caches message data in a size-managed (no memory leaks) and per-message mutex-protected (no race conditions) global dictionary to maximize efficiency and minimize Discord API calls
- Fully asynchronous

## Instructions
Before you start, install Python and clone this git repo.

1. Install Python requirements: `pip install -r requirements.txt`

2. Create a copy of *.env.example* named *.env* and set it up (see below)

3. Run the bot: `python llmcord.py`

| Setting | Instructions |
| --- | --- |
| **DISCORD_BOT_TOKEN** | Create a new Discord bot at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the **Bot** tab. Also enable **MESSAGE CONTENT INTENT**. |
| **DISCORD_CLIENT_ID** | Found under the **OAuth2** tab of the Discord bot you just made. |
| **LLM** | For [LiteLLM supported providers](https://docs.litellm.ai/docs/providers) ([OpenAI API](https://docs.litellm.ai/docs/providers/openai), [Mistral API](https://docs.litellm.ai/docs/providers/mistral), [ollama](https://docs.litellm.ai/docs/providers/ollama), etc.), follow the LiteLLM instructions for its model name formatting.<br /><br />For local models (running on an OpenAI compatible API server), set to **`local/openai/model`**. If using a vision model, set to **`local/openai/vision-model`**. Some setups will instead require **`local/openai/<MODEL_NAME>`** where **<MODEL_NAME>** is the exact name of the model you're using. |
| **LLM_MAX_TOKENS** | The maximum number of tokens in the LLM's chat completion.<br />(Default: `1024`) |
| **LLM_TEMPERATURE** | LLM sampling temperature. Higher values make the LLM's output more random.<br />(Default: `1.0`) |
| **LLM_TOP_P** | LLM nucleus sampling value. **Alternative to sampling temperature.** Higher values make the LLM's output more diverse.<br />(Default: `1.0`) |
| **CUSTOM_SYSTEM_PROMPT** | Write practically anything you want to customize the bot's behavior! |
| **CUSTOM_DISCORD_STATUS** | Set a custom message that displays on the bot's Discord profile. **Max 128 characters.** |
| **ALLOWED_CHANNEL_IDS** | Discord channel IDs where the bot can send messages, separated by commas. **Leave blank to allow all channels.** |
| **ALLOWED_ROLE_IDS** | Discord role IDs that can use the bot, separated by commas. **Leave blank to allow everyone. Specifying at least one role also disables DMs.** |
| **MAX_IMAGES** | The maximum number of image attachments allowed in a single message. **Only applicable when using a vision model.**<br />(Default: `5`) |
| **MAX_MESSAGES** | The maximum number of messages allowed in a reply chain.<br />(Default: `20`) |
| **LOCAL_SERVER_URL** | The URL of your local API server. **Only applicable when using a local model.**<br />(Default: `http://localhost:5000/v1`) |
| **LOCAL_API_KEY** | The API key to use with your local API server. **Only applicable when using a local model. Usually safe to leave blank.** |
| **OOBABOOGA_CHARACTER** | Your [oobabooga character](https://github.com/oobabooga/text-generation-webui/wiki/03-%E2%80%90-Parameters-Tab#character) that you want to use. **Only applicable when using oobabooga. Leave blank to use CUSTOM_SYSTEM_PROMPT instead.** |
| **OPENAI_API_KEY** | **Only required if you choose an OpenAI API model.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL_API_KEY** | **Only required if you choose a Mistral API model.** Generate a Mistral API key at [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|

> **OPENAI_API_KEY** and **MISTRAL_API_KEY** are provided as examples. Add more as needed for other [LiteLLM providers](https://docs.litellm.ai/docs/providers).

## Notes
- Only models from OpenAI API are user identity aware because only OpenAI supports the message "name" property. Hopefully others support this in the future.

- PRs are welcome :)

## Star History
<a href="https://star-history.com/#jakobdylanc/discord-llm-chatbot&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
  </picture>
</a>
