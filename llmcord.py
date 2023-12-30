import asyncio
import logging
import os
from time import time

import discord
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

LLM_CONFIG = {
    "gpt": {
        "api_key": os.environ["OPENAI_API_KEY"],
        "base_url": "https://api.openai.com/v1",
    },
    "mistral": {
        "api_key": os.environ["MISTRAL_API_KEY"],
        "base_url": "https://api.mistral.ai/v1",
    },
}
SYSTEM_PROMPT = {
    "role": "system",
    "content": f"{os.environ['CUSTOM_SYSTEM_PROMPT']}\nUser's names are their Discord IDs and should be typed as '<@ID>'.",
}
if os.environ["LLM"] == "gpt-4-vision-preview" or "mistral-" in os.environ["LLM"]:
    # Temporary fix until gpt-4-vision-preview and Mistral API support message.name
    SYSTEM_PROMPT = {
        "role": "system",
        "content": os.environ["CUSTOM_SYSTEM_PROMPT"],
    }

LLM_VISION_SUPPORT = "vision" in os.environ["LLM"]
MAX_IMAGES = int(os.environ["MAX_IMAGES"]) if LLM_VISION_SUPPORT else 0
MAX_MESSAGES = int(os.environ["MAX_MESSAGES"])
MAX_IMAGE_WARNING = f"⚠️ Max {MAX_IMAGES} image{'' if MAX_IMAGES == 1 else 's'} per message" if MAX_IMAGES > 0 else "⚠️ Can't see images"
MAX_MESSAGE_WARNING = f"⚠️ Only using last {MAX_MESSAGES} messages"
MAX_COMPLETION_TOKENS = 1024
EMBED_COLOR = {"incomplete": discord.Color.orange(), "complete": discord.Color.green()}
EMBED_MAX_LENGTH = 4096
EDITS_PER_SECOND = 1.3

llm_client = AsyncOpenAI(**LLM_CONFIG[os.environ["LLM"].split("-", 1)[0]])
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

message_nodes = {}
in_progress_message_ids = []


class MessageNode:
    def __init__(self, message, too_many_images=False, replied_to=None):
        self.message = message
        self.too_many_images = too_many_images
        self.replied_to = replied_to


@discord_client.event
async def on_message(message):
    # Filter out unwanted messages
    if (message.channel.type != discord.ChannelType.private and discord_client.user not in message.mentions) or message.author.bot:
        return

    # If user replied to a message that's still generating, wait until it's done
    while message.reference and message.reference.message_id in in_progress_message_ids:
        await asyncio.sleep(0)

    async with message.channel.typing():
        # Loop through message reply chain and create MessageNodes
        current_message = message
        previous_message_id = None
        while True:
            current_message_text = current_message.embeds[0].description if current_message.author == discord_client.user else current_message.content
            if current_message_text.startswith(discord_client.user.mention):
                current_message_text = current_message_text[len(discord_client.user.mention) :].lstrip()
            current_message_content = [{"type": "text", "text": current_message_text}] if current_message_text else []
            current_message_images = [
                {
                    "type": "image_url",
                    "image_url": {"url": att.url, "detail": "low"},
                }
                for att in current_message.attachments
                if "image" in att.content_type
            ]
            current_message_content += current_message_images[:MAX_IMAGES]
            if "mistral" in os.environ["LLM"]:
                # Temporary fix until Mistral API supports message.content as a list
                current_message_content = current_message_text
            current_message_author_role = "assistant" if current_message.author == discord_client.user else "user"
            message_nodes[current_message.id] = MessageNode(
                {
                    "role": current_message_author_role,
                    "content": current_message_content,
                    "name": str(current_message.author.id),
                }
            )
            if len(current_message_images) > MAX_IMAGES:
                message_nodes[current_message.id].too_many_images = True
            if previous_message_id:
                message_nodes[previous_message_id].replied_to = message_nodes[current_message.id]
            if not current_message.reference:
                break
            if current_message.reference.message_id in message_nodes:
                message_nodes[current_message.id].replied_to = message_nodes[current_message.reference.message_id]
                break
            previous_message_id = current_message.id
            try:
                current_message = (
                    current_message.reference.resolved
                    if isinstance(current_message.reference.resolved, discord.Message)
                    else await message.channel.fetch_message(current_message.reference.message_id)
                )
            except (discord.NotFound, discord.HTTPException):
                break

        # Build conversation history from reply chain and set user warnings
        reply_chain = []
        user_warnings = set()
        current_node = message_nodes[message.id]
        while current_node is not None and len(reply_chain) < MAX_MESSAGES:
            reply_chain += [current_node.message]
            if current_node.too_many_images:
                user_warnings.add(MAX_IMAGE_WARNING)
            if len(reply_chain) == MAX_MESSAGES and current_node.replied_to:
                user_warnings.add(MAX_MESSAGE_WARNING)
            current_node = current_node.replied_to
        messages = [SYSTEM_PROMPT] + reply_chain[::-1]

        # Generate and send bot reply
        logging.info(f"Message received: {reply_chain[0]}, reply chain length: {len(reply_chain)}")
        response_messages = []
        response_message_contents = []
        previous_content = None
        edit_message_task = None
        async for chunk in await llm_client.chat.completions.create(
            model=os.environ["LLM"],
            messages=messages,
            max_tokens=MAX_COMPLETION_TOKENS,
            stream=True,
        ):
            current_content = chunk.choices[0].delta.content or ""
            if previous_content:
                if not response_messages or len(response_message_contents[-1] + previous_content) > EMBED_MAX_LENGTH:
                    reply_message = message if not response_messages else response_messages[-1]
                    embed_color = EMBED_COLOR["complete"] if current_content == "" else EMBED_COLOR["incomplete"]
                    embed = discord.Embed(description=previous_content, color=embed_color)
                    if user_warnings:
                        embed.set_footer(text="\n".join(sorted(user_warnings)))
                    response_messages += [
                        await reply_message.reply(
                            embed=embed,
                            silent=True,
                        )
                    ]
                    in_progress_message_ids.append(response_messages[-1].id)
                    last_message_task_time = time()
                    response_message_contents += [""]
                response_message_contents[-1] += previous_content
                if response_message_contents[-1] != previous_content:
                    final_message_edit = len(response_message_contents[-1] + current_content) > EMBED_MAX_LENGTH or current_content == ""
                    if (
                        final_message_edit
                        or (not edit_message_task or edit_message_task.done())
                        and time() - last_message_task_time >= len(in_progress_message_ids) / EDITS_PER_SECOND
                    ):
                        while edit_message_task and not edit_message_task.done():
                            await asyncio.sleep(0)
                        embed_color = EMBED_COLOR["complete"] if final_message_edit else EMBED_COLOR["incomplete"]
                        embed.description = response_message_contents[-1]
                        embed.color = embed_color
                        edit_message_task = asyncio.create_task(response_messages[-1].edit(embed=embed))
                        last_message_task_time = time()
            previous_content = current_content

        # Create MessageNode(s) for bot reply message(s) (can be multiple if bot reply was long)
        for response_message in response_messages:
            message_nodes[response_message.id] = MessageNode(
                {
                    "role": "assistant",
                    "content": "".join(response_message_contents),
                    "name": str(discord_client.user.id),
                },
                replied_to=message_nodes[message.id],
            )
            in_progress_message_ids.remove(response_message.id)


async def main():
    await discord_client.start(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
