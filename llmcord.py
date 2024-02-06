import asyncio
from datetime import datetime as dt
import logging
import os

import discord
from dotenv import load_dotenv
from litellm import acompletion

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)

LLM_VISION_SUPPORT: bool = "gpt-4-vision-preview" in os.environ["LLM"]
MAX_COMPLETION_TOKENS = 1024

ALLOWED_CHANNEL_TYPES = (discord.ChannelType.text, discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.private)
ALLOWED_CHANNEL_IDS = tuple(int(i) for i in os.environ["ALLOWED_CHANNEL_IDS"].split(",") if i)
ALLOWED_ROLE_IDS = tuple(int(i) for i in os.environ["ALLOWED_ROLE_IDS"].split(",") if i)
MAX_IMAGES = int(os.environ["MAX_IMAGES"]) if LLM_VISION_SUPPORT else 0
MAX_MESSAGES = int(os.environ["MAX_MESSAGES"])
MAX_IMAGE_WARNING = f"⚠️ Max {MAX_IMAGES} image{'' if MAX_IMAGES == 1 else 's'} per message" if MAX_IMAGES > 0 else "⚠️ Can't see images"
MAX_MESSAGE_WARNING = f"⚠️ Only using last {MAX_MESSAGES} messages"

EMBED_COLOR = {"incomplete": discord.Color.orange(), "complete": discord.Color.green()}
EMBED_MAX_LENGTH = 4096
EDITS_PER_SECOND = 1.3

system_prompt_extras = []
if any(os.environ["LLM"].startswith(x) for x in ("gpt", "openai/gpt")) and "gpt-4-vision-preview" not in os.environ["LLM"]:
    system_prompt_extras.append("User's names are their Discord IDs and should be typed as '<@ID>'.")

extra_kwargs = {}
if os.environ["LLM"].startswith("local"):
    extra_kwargs["base_url"] = os.environ["LOCAL_SERVER_URL"]
    os.environ["LLM"] = os.environ["LLM"].replace("local", "openai", 1)

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents, activity=discord.CustomActivity(name="github.com/jakobdylanc/discord-llm-chatbot"))

msg_nodes = {}
active_msg_ids = []


class MsgNode:
    def __init__(self, data, too_many_images=False, replied_to_id=None):
        self.data = data
        self.too_many_images = too_many_images
        self.replied_to_id = replied_to_id


def get_system_prompt():
    return [
        {
            "role": "system",
            "content": "\n".join([os.environ["CUSTOM_SYSTEM_PROMPT"]] + system_prompt_extras + [f"Today's date: {dt.now().strftime('%B %d %Y')}"]),
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

    # Loop through message reply chain and create MsgNodes (until an existing MsgNode is found)
    curr_msg = msg
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

        next_is_thread_parent: bool = curr_msg.channel.type == discord.ChannelType.public_thread and not curr_msg.reference
        msg_nodes[curr_msg.id].replied_to_id = curr_msg.channel.id if next_is_thread_parent else getattr(curr_msg.reference, "message_id", None)
        if not (next_id := msg_nodes[curr_msg.id].replied_to_id) or next_id in msg_nodes:
            break
        while next_id in active_msg_ids:
            await asyncio.sleep(0)
        try:
            curr_msg = (
                (curr_msg.channel.starter_message or await curr_msg.channel.parent.fetch_message(next_id))
                if next_is_thread_parent
                else (ref if isinstance(ref := curr_msg.reference.resolved, discord.Message) else await curr_msg.channel.fetch_message(next_id))
            )
        except (discord.NotFound, discord.HTTPException, AttributeError):
            break

    # Build reply chain and set user warnings
    reply_chain = []
    user_warnings = set()
    curr_node = msg_nodes[msg.id]
    while len(reply_chain) < MAX_MESSAGES:
        reply_chain += [curr_node.data]
        if curr_node.too_many_images:
            user_warnings.add(MAX_IMAGE_WARNING)
        if len(reply_chain) == MAX_MESSAGES and curr_node.replied_to_id:
            user_warnings.add(MAX_MESSAGE_WARNING)
        if not curr_node.replied_to_id:
            break
        curr_node = msg_nodes[curr_node.replied_to_id]

    # Generate and send bot reply
    logging.info(f"Message received: {reply_chain[0]}, reply chain length: {len(reply_chain)}")
    response_msgs = []
    response_contents = []
    prev_content = None
    edit_task = None
    kwargs = dict(model=os.environ["LLM"], messages=(get_system_prompt() + reply_chain[::-1]), max_tokens=MAX_COMPLETION_TOKENS, stream=True) | extra_kwargs
    async with msg.channel.typing():
        try:
            async for chunk in await acompletion(**kwargs):
                curr_content = chunk.choices[0].delta.content or ""
                if not prev_content:
                    prev_content = curr_content
                    continue

                if not response_msgs or len(response_contents[-1] + prev_content) > EMBED_MAX_LENGTH:
                    reply_to_msg = msg if not response_msgs else response_msgs[-1]
                    embed = discord.Embed(description="⏳", color=EMBED_COLOR["incomplete"])
                    for warning in sorted(user_warnings):
                        embed.add_field(name=warning, value="", inline=False)
                    response_msgs += [
                        await reply_to_msg.reply(
                            embed=embed,
                            silent=True,
                        )
                    ]
                    active_msg_ids.append(response_msgs[-1].id)
                    last_task_time = dt.now().timestamp()
                    response_contents += [""]

                response_contents[-1] += prev_content
                is_final_edit: bool = chunk.choices[0].finish_reason or len(response_contents[-1] + curr_content) > EMBED_MAX_LENGTH
                if is_final_edit or (not edit_task or edit_task.done()) and dt.now().timestamp() - last_task_time >= len(active_msg_ids) / EDITS_PER_SECOND:
                    while edit_task and not edit_task.done():
                        await asyncio.sleep(0)
                    if response_contents[-1].strip():
                        embed.description = response_contents[-1]
                    embed.color = EMBED_COLOR["complete"] if is_final_edit else EMBED_COLOR["incomplete"]
                    edit_task = asyncio.create_task(response_msgs[-1].edit(embed=embed))
                    last_task_time = dt.now().timestamp()

                prev_content = curr_content
        except:
            logging.exception("Error while streaming response")

    # Create MsgNode(s) for bot reply message(s) (can be multiple if bot reply was long)
    for response_msg in response_msgs:
        msg_nodes[response_msg.id] = MsgNode(
            {
                "role": "assistant",
                "content": "".join(response_contents),
                "name": str(discord_client.user.id),
            },
            replied_to_id=msg.id,
        )
        active_msg_ids.remove(response_msg.id)


async def main():
    await discord_client.start(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
