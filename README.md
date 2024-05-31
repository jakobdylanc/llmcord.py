<h1 align="center">
  llmcord.py
</h1>

<h3 align="center"><i>
  Talk to LLMs with your friends!
</i></h3>

<p align="center">
  <img src="https://github.com/jakobdylanc/discord-llm-chatbot/assets/38699060/789d49fe-ef5c-470e-b60e-48ac03057443" alt="">
</p>

llmcord.py lets you and your friends chat with LLMs directly in your Discord server. It works with practically any LLM, remote or locally hosted.

## Features
### Reply-based chat system
Just @ the bot to start a conversation and reply to continue. Build conversations with reply chains!

You can do things like:
- Continue your own conversation or someone else's
- "Rewind" a conversation by simply replying to an older message
- @ the bot while replying to any message in your server to ask a question about it

Additionally:
- Back-to-back messages from the same user are automatically chained together. Just reply to the latest one and the bot will see all of them.
- You can seamlessly move any conversation into a [thread](https://support.discord.com/hc/en-us/articles/4403205878423-Threads-FAQ). Just create a thread from any message and @ the bot inside to continue.

### Choose any LLM
llmcord.py supports remote models from [OpenAI API](https://platform.openai.com/docs/models), [Mistral API](https://docs.mistral.ai/platform/endpoints), [Anthropic API](https://docs.anthropic.com/claude/docs/models-overview) and [many more](https://docs.litellm.ai/docs/providers) thanks to [LiteLLM](https://github.com/BerriAI/litellm).

Or run a local model with [ollama](https://ollama.com), [oobabooga](https://github.com/oobabooga/text-generation-webui), [Jan](https://jan.ai), [LM Studio](https://lmstudio.ai) or any other OpenAI compatible API server.

### And more:
- Supports image attachments when using a vision model (like gpt-4o, claude-3, llava, etc.)
- Supports text file attachments (.txt, .py, .c, etc.)
- Customizable system prompt
- DM for private access (no @ required)
- User identity aware (OpenAI API only)
- Streamed responses (turns green when complete, automatically splits into separate messages when too long, throttled to prevent Discord ratelimiting)
- Displays helpful user warnings when appropriate (like "Only using last 20 messages" when the customizable message limit is exceeded)
- Caches message data in a size-managed (no memory leaks) and per-message mutex-protected (no race conditions) global dictionary to maximize efficiency and minimize Discord API calls
- Fully asynchronous
- 1 Python file, ~200 lines of code

## Instructions
Before you start, install Python and clone this git repo.

1. Install Python requirements: `pip install -U -r requirements.txt`

2. Create a copy of ".env.example" named ".env" and set it up (see below)

3. Run the bot: `python llmcord.py` (the invite URL will print to the console)

| Setting | Instructions |
| --- | --- |
| **DISCORD_BOT_TOKEN** | Create a new Discord bot at [discord.com/developers/applications](https://discord.com/developers/applications) and generate a token under the "Bot" tab. Also enable "MESSAGE CONTENT INTENT". |
| **DISCORD_CLIENT_ID** | Found under the "OAuth2" tab of the Discord bot you just made. |
| **DISCORD_STATUS_MESSAGE** | Set a custom message that displays on the bot's Discord profile. **Max 128 characters.** |
| **LLM** | For [LiteLLM supported providers](https://docs.litellm.ai/docs/providers) ([OpenAI API](https://docs.litellm.ai/docs/providers/openai), [Mistral API](https://docs.litellm.ai/docs/providers/mistral), [ollama](https://docs.litellm.ai/docs/providers/ollama), etc.), follow the LiteLLM instructions for its model name formatting.<br /><br />For local models ([oobabooga](https://github.com/oobabooga/text-generation-webui), [Jan](https://jan.ai), [LM Studio](https://lmstudio.ai), etc.), set to `local/openai/model` (or `local/openai/vision-model` if using a vision model). Some setups will instead require `local/openai/<MODEL_NAME>` where <MODEL_NAME> is the exact name of the model you're using. |
| **LLM_SETTINGS** | Extra API parameters for your LLM, separated by commas.<br />(Default: `max_tokens=1024, temperature=1.0`) |
| **LLM_SYSTEM_PROMPT** | Write anything you want to customize the bot's behavior! |
| **LOCAL_SERVER_URL** | The URL of your local API server. **Only applicable when "LLM" starts with `local/`.**<br />(Default: `http://localhost:5000/v1`) |
| **ALLOWED_CHANNEL_IDS** | Discord channel IDs where the bot can send messages, separated by commas. **Leave blank to allow all channels.** |
| **ALLOWED_ROLE_IDS** | Discord role IDs that can use the bot, separated by commas. **Leave blank to allow everyone. Specifying at least one role also disables DMs.** |
| **MAX_TEXT** | The maximum amount of text allowed in a single message, including text from file attachments.<br />(Default: `100000`) |
| **MAX_IMAGES** | The maximum number of image attachments allowed in a single message. **Only applicable when using a vision model.**<br />(Default: `5`) |
| **MAX_MESSAGES** | The maximum number of messages allowed in a reply chain.<br />(Default: `20`) |
| **OPENAI_API_KEY** | **Only required if you choose a model from OpenAI API.** Generate an OpenAI API key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys). You must also add a payment method to your OpenAI account at [platform.openai.com/account/billing/payment-methods](https://platform.openai.com/account/billing/payment-methods).|
| **MISTRAL_API_KEY** | **Only required if you choose a model from Mistral API.** Generate a Mistral API key at [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys). You must also add a payment method to your Mistral account at [console.mistral.ai/billing](https://console.mistral.ai/billing).|

> **OPENAI_API_KEY** and **MISTRAL_API_KEY** are provided as examples. Add more as needed for other [LiteLLM supported providers](https://docs.litellm.ai/docs/providers).

## Notes
- If you're having issues, try my suggestions [here](https://github.com/jakobdylanc/discord-llm-chatbot/issues/19)

- Only models from OpenAI are "user identity aware" because only OpenAI API supports the message "name" property. Hopefully others support this in the future.

- PRs are welcome :)

## Star History
<a href="https://star-history.com/#jakobdylanc/discord-llm-chatbot&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jakobdylanc/discord-llm-chatbot&type=Date" />
  </picture>
</a>
