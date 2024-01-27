import asyncio
from datetime import datetime
import logging
import os

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
    "local": {
        "api_key": "Not used",
        "base_url": os.environ["LOCAL_SERVER_URL"],
    },
}
LLM_PROVIDER = os.environ["LLM"].split("-", 1)[0]
LLM_VISION_SUPPORT = "vision" in os.environ["LLM"]
MAX_COMPLETION_TOKENS = 1024

ALLOWED_CHANNEL_TYPES = (discord.ChannelType.text, discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.private)
ALLOWED_CHANNEL_IDS = tuple(int(i) for i in os.environ["ALLOWED_CHANNEL_IDS"].split(",") if i)
ALLOWED_ROLE_IDS = tuple(int(i) for i in os.environ["ALLOWED_ROLE_IDS"].split(",") if i)
MAX_IMAGES = int(os.environ["MAX_IMAGES"]) if LLM_VISION_SUPPORT else 0
MAX_IMAGE_WARNING = f"⚠️ Max {MAX_IMAGES} image{'' if MAX_IMAGES == 1 else 's'} per message" if MAX_IMAGES > 0 else "⚠️ Can't see images"
MAX_MESSAGES = int(os.environ["MAX_MESSAGES"])
MAX_MESSAGE_WARNING = f"⚠️ Only using last {MAX_MESSAGES} messages"

EMBED_COLOR = {"incomplete": discord.Color.orange(), "complete": discord.Color.green()}
EMBED_MAX_LENGTH = 4096
EDITS_PER_SECOND = 1.3

llm_client = AsyncOpenAI(**LLM_CONFIG[LLM_PROVIDER])
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

msg_nodes = {}
active_msg_ids = []


class MsgNode:
    def __init__(self, msg, too_many_images=False, replied_to=None):
        self.msg = msg
        self.too_many_images = too_many_images
        self.replied_to = replied_to


def get_system_prompt():
    system_prompt_extras = [f"Today's date: {datetime.now().strftime('%B %d %Y')}"]
    if LLM_PROVIDER == "gpt" and os.environ["LLM"] != "gpt-4-vision-preview":
        system_prompt_extras.append("User's names are their Discord IDs and should be typed as '<@ID>'.")
    return [
        {
            "role": "system",
            "content": "\n".join([os.environ["CUSTOM_SYSTEM_PROMPT"]] + system_prompt_extras),
        }
    ]


@discord_client.event
async def on_message(msg):
    # Filter out unwanted messages
    if (
        msg.channel.type not in ALLOWED_CHANNEL_TYPES
        or (msg.channel.type != discord.ChannelType.private and discord_client.user not in msg.mentions)
        or (ALLOWED_CHANNEL_IDS and not any(id in ALLOWED_CHANNEL_IDS for id in (msg.channel.id, getattr(msg.channel, "parent_id", None))))
        or (ALLOWED_ROLE_IDS and (msg.channel.type == discord.ChannelType.private or not any(role.id in ALLOWED_ROLE_IDS for role in msg.author.roles)))
        or msg.author.bot
    ):
        return

    # If user replied to a message that's still generating, wait until it's done
    while msg.reference and msg.reference.message_id in active_msg_ids:
        await asyncio.sleep(0)

    async with msg.channel.typing():
        # Loop through message reply chain and create MsgNodes
        curr_msg = msg
        prev_msg_id = None
        while True:
            curr_msg_role = "assistant" if curr_msg.author == discord_client.user else "user"
            curr_msg_content = curr_msg.embeds[0].description if curr_msg.embeds and curr_msg.author.bot else curr_msg.content
            if curr_msg_content.startswith(discord_client.user.mention):
                curr_msg_content = curr_msg_content[len(discord_client.user.mention) :].lstrip()
            curr_msg_images = [
                {
                    "type": "image_url",
                    "image_url": {"url": att.url, "detail": "low"},
                }
                for att in curr_msg.attachments
                if "image" in att.content_type
            ]
            if LLM_VISION_SUPPORT:
                curr_msg_content = ([{"type": "text", "text": curr_msg_content}] if curr_msg_content else []) + curr_msg_images[:MAX_IMAGES]
            msg_nodes[curr_msg.id] = MsgNode(
                {
                    "role": curr_msg_role,
                    "content": curr_msg_content,
                    "name": str(curr_msg.author.id),
                },
                too_many_images=len(curr_msg_images) > MAX_IMAGES,
            )
            if prev_msg_id:
                msg_nodes[prev_msg_id].replied_to = msg_nodes[curr_msg.id]
            prev_msg_id = curr_msg.id
            if not curr_msg.reference and curr_msg.channel.type == discord.ChannelType.public_thread:
                try:
                    thread_parent_msg = curr_msg.channel.starter_message or await curr_msg.channel.parent.fetch_message(curr_msg.channel.id)
                except (discord.NotFound, discord.HTTPException, AttributeError):
                    break
                if thread_parent_msg.id in msg_nodes:
                    msg_nodes[curr_msg.id].replied_to = msg_nodes[thread_parent_msg.id]
                    break
                curr_msg = thread_parent_msg
            else:
                if not curr_msg.reference:
                    break
                if curr_msg.reference.message_id in msg_nodes:
                    msg_nodes[curr_msg.id].replied_to = msg_nodes[curr_msg.reference.message_id]
                    break
                try:
                    curr_msg = curr_msg.reference.resolved if isinstance(curr_msg.reference.resolved, discord.Message) else await curr_msg.channel.fetch_message(curr_msg.reference.message_id)
                except (discord.NotFound, discord.HTTPException):
                    break

        # Build reply chain and set user warnings
        reply_chain = []
        user_warnings = set()
        curr_node = msg_nodes[msg.id]
        while curr_node is not None and len(reply_chain) < MAX_MESSAGES:
            reply_chain += [curr_node.msg]
            if curr_node.too_many_images:
                user_warnings.add(MAX_IMAGE_WARNING)
            if len(reply_chain) == MAX_MESSAGES and curr_node.replied_to:
                user_warnings.add(MAX_MESSAGE_WARNING)
            curr_node = curr_node.replied_to

        # Generate and send bot reply
        logging.info(f"Message received: {reply_chain[0]}, reply chain length: {len(reply_chain)}")
        response_msgs = []
        response_contents = []
        prev_content = None
        edit_task = None
        async for chunk in await llm_client.chat.completions.create(
            model=os.environ["LLM"],
            messages=get_system_prompt() + reply_chain[::-1],
            max_tokens=MAX_COMPLETION_TOKENS,
            stream=True,
        ):
            curr_content = chunk.choices[0].delta.content or ""
            if prev_content:
                if not response_msgs or len(response_contents[-1] + prev_content) > EMBED_MAX_LENGTH:
                    reply_msg = msg if not response_msgs else response_msgs[-1]
                    embed = discord.Embed(description="⏳", color=EMBED_COLOR["incomplete"])
                    for warning in sorted(user_warnings):
                        embed.add_field(name=warning, value="", inline=False)
                    response_msgs += [
                        await reply_msg.reply(
                            embed=embed,
                            silent=True,
                        )
                    ]
                    active_msg_ids.append(response_msgs[-1].id)
                    last_task_time = datetime.now().timestamp()
                    response_contents += [""]
                response_contents[-1] += prev_content
                final_edit = len(response_contents[-1] + curr_content) > EMBED_MAX_LENGTH or curr_content == ""
                if final_edit or (not edit_task or edit_task.done()) and datetime.now().timestamp() - last_task_time >= len(active_msg_ids) / EDITS_PER_SECOND:
                    while edit_task and not edit_task.done():
                        await asyncio.sleep(0)
                    if response_contents[-1].strip():
                        embed.description = response_contents[-1]
                    embed.color = EMBED_COLOR["complete"] if final_edit else EMBED_COLOR["incomplete"]
                    edit_task = asyncio.create_task(response_msgs[-1].edit(embed=embed))
                    last_task_time = datetime.now().timestamp()
            prev_content = curr_content

    # Create MsgNode(s) for bot reply message(s) (can be multiple if bot reply was long)
    for response_msg in response_msgs:
        msg_nodes[response_msg.id] = MsgNode(
            {
                "role": "assistant",
                "content": "".join(response_contents),
                "name": str(discord_client.user.id),
            },
            replied_to=msg_nodes[msg.id],
        )
        active_msg_ids.remove(response_msg.id)


async def main():
    await discord_client.start(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
