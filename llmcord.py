import asyncio
import base64
from dataclasses import dataclass, field
from datetime import datetime as dt
import json
import logging
from os import environ as env
import requests
from typing import Optional

import discord
from dotenv import load_dotenv
from litellm import acompletion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

load_dotenv()
with open("config.json", "r") as file:
    config = {k: v for d in json.load(file).values() for k, v in d.items()}

llm = config["llm"]

LLM_IS_LOCAL: bool = llm.startswith("local/")
LLM_ACCEPTS_IMAGES: bool = any(x in llm for x in ("claude-3", "gpt-4-turbo", "gpt-4o", "llava", "vision"))
LLM_ACCEPTS_NAMES: bool = any(llm.startswith(x) for x in ("gpt", "openai/gpt"))

ALLOWED_FILE_TYPES = ("image", "text")
ALLOWED_CHANNEL_TYPES = (discord.ChannelType.text, discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.private)
ALLOWED_CHANNEL_IDS = config["allowed_channel_ids"]
ALLOWED_ROLE_IDS = config["allowed_role_ids"]

MAX_TEXT = config["max_text"]
MAX_IMAGES = config["max_images"] if LLM_ACCEPTS_IMAGES else 0
MAX_MESSAGES = config["max_messages"]

EMBED_COLOR_COMPLETE = discord.Color.dark_green()
EMBED_COLOR_INCOMPLETE = discord.Color.orange()
EMBED_MAX_LENGTH = 4096
EDIT_DELAY_SECONDS = 1.3
MAX_MESSAGE_NODES = 100

extra_api_parameters = config["extra_api_parameters"]

if LLM_IS_LOCAL:
    extra_api_parameters["base_url"] = config["local_server_url"]
    if "api_key" not in extra_api_parameters:
        extra_api_parameters["api_key"] = "Not used"

    llm = llm.replace("local/", "", 1)

if config["client_id"] != 123456789:
    print(f"\nBOT INVITE URL:\nhttps://discord.com/api/oauth2/authorize?client_id={config['client_id']}&permissions=412317273088&scope=bot\n")

intents = discord.Intents.default()
intents.message_content = True
activity = discord.CustomActivity(name=config["status_message"][:128] or "github.com/jakobdylanc/discord-llm-chatbot")
bot = discord.Client(intents=intents, activity=activity)

msg_nodes = {}
last_task_time = None


@dataclass
class MsgNode:
    data: dict = field(default_factory=dict)
    next_msg: Optional[discord.Message] = None

    too_much_text: bool = False
    too_many_images: bool = False
    has_bad_attachments: bool = False
    fetch_next_failed: bool = False

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def get_system_prompt():
    system_prompt_extras = [f"Today's date: {dt.now().strftime('%B %d %Y')}"]
    if LLM_ACCEPTS_NAMES:
        system_prompt_extras += ["User's names are their Discord IDs and should be typed as '<@ID>'."]

    return [
        {
            "role": "system",
            "content": "\n".join([config["system_prompt"]] + system_prompt_extras),
        }
    ]


@bot.event
async def on_message(new_msg):
    global msg_nodes, last_task_time

    # Filter out unwanted messages
    if (
        new_msg.channel.type not in ALLOWED_CHANNEL_TYPES
        or (new_msg.channel.type != discord.ChannelType.private and bot.user not in new_msg.mentions)
        or (ALLOWED_CHANNEL_IDS and not any(id in ALLOWED_CHANNEL_IDS for id in (new_msg.channel.id, getattr(new_msg.channel, "parent_id", None))))
        or (ALLOWED_ROLE_IDS and (new_msg.channel.type == discord.ChannelType.private or not any(role.id in ALLOWED_ROLE_IDS for role in new_msg.author.roles)))
        or new_msg.author.bot
    ):
        return

    # Build message reply chain and set user warnings
    reply_chain = []
    user_warnings = set()
    curr_msg = new_msg
    while curr_msg and len(reply_chain) < MAX_MESSAGES:
        async with msg_nodes.setdefault(curr_msg.id, MsgNode()).lock:
            curr_node = msg_nodes[curr_msg.id]

            if not curr_node.data:
                good_attachments = {type: [att for att in curr_msg.attachments if att.content_type and type in att.content_type] for type in ALLOWED_FILE_TYPES}

                text = "\n".join(
                    ([curr_msg.content] if curr_msg.content else [])
                    + [embed.description for embed in curr_msg.embeds if embed.description]
                    + [requests.get(att.url).text for att in good_attachments["text"]]
                )
                if curr_msg.content.startswith(bot.user.mention):
                    text = text.replace(bot.user.mention, "", 1).lstrip()

                if LLM_ACCEPTS_IMAGES and good_attachments["image"][:MAX_IMAGES]:
                    content = ([{"type": "text", "text": text[:MAX_TEXT]}] if text[:MAX_TEXT] else []) + [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{att.content_type};base64,{base64.b64encode(requests.get(att.url).content).decode('utf-8')}"},
                        }
                        for att in good_attachments["image"][:MAX_IMAGES]
                    ]
                else:
                    content = text[:MAX_TEXT]

                data = {
                    "content": content,
                    "role": "assistant" if curr_msg.author == bot.user else "user",
                }
                if LLM_ACCEPTS_NAMES:
                    data["name"] = str(curr_msg.author.id)

                curr_node.data = data
                curr_node.too_much_text = len(text) > MAX_TEXT
                curr_node.too_many_images = len(good_attachments["image"]) > MAX_IMAGES
                curr_node.has_bad_attachments = len(curr_msg.attachments) > sum(len(att_list) for att_list in good_attachments.values())

                try:
                    if (
                        not curr_msg.reference
                        and curr_msg.channel.type != discord.ChannelType.private
                        and bot.user.mention not in curr_msg.content
                        and (prev_msg_in_channel := ([m async for m in curr_msg.channel.history(before=curr_msg, limit=1)] or [None])[0])
                        and any(prev_msg_in_channel.type == type for type in (discord.MessageType.default, discord.MessageType.reply))
                        and prev_msg_in_channel.author == curr_msg.author
                    ):
                        curr_node.next_msg = prev_msg_in_channel
                    else:
                        next_is_thread_parent: bool = not curr_msg.reference and curr_msg.channel.type == discord.ChannelType.public_thread
                        if next_msg_id := curr_msg.channel.id if next_is_thread_parent else getattr(curr_msg.reference, "message_id", None):
                            while msg_nodes.setdefault(next_msg_id, MsgNode()).lock.locked():
                                await asyncio.sleep(0)
                            curr_node.next_msg = (
                                (curr_msg.channel.starter_message or await curr_msg.channel.parent.fetch_message(next_msg_id))
                                if next_is_thread_parent
                                else (curr_msg.reference.cached_message or await curr_msg.channel.fetch_message(next_msg_id))
                            )
                except (discord.NotFound, discord.HTTPException, AttributeError):
                    logging.exception("Error fetching next message in the chain")
                    curr_node.fetch_next_failed = True

            if curr_node.data["content"]:
                reply_chain += [curr_node.data]

            if curr_node.too_much_text:
                user_warnings.add(f"⚠️ Max {MAX_TEXT:,} characters per message")
            if curr_node.too_many_images:
                user_warnings.add(f"⚠️ Max {MAX_IMAGES} image{'' if MAX_IMAGES == 1 else 's'} per message" if MAX_IMAGES > 0 else "⚠️ Can't see images")
            if curr_node.has_bad_attachments:
                user_warnings.add("⚠️ Unsupported attachments")
            if curr_node.fetch_next_failed or (curr_node.next_msg and len(reply_chain) == MAX_MESSAGES):
                user_warnings.add(f"⚠️ Only using last {len(reply_chain)} message{'' if len(reply_chain) == 1 else 's'}")

            curr_msg = curr_node.next_msg

    logging.info(f"Message received (user ID: {new_msg.author.id}, attachments: {len(new_msg.attachments)}, reply chain length: {len(reply_chain)}):\n{new_msg.content}")

    # Generate and send response message(s) (can be multiple if response is long)
    response_msgs = []
    response_contents = []
    prev_chunk = None
    edit_task = None
    kwargs = dict(model=llm, messages=(get_system_prompt() + reply_chain[::-1]), stream=True) | extra_api_parameters
    try:
        async with new_msg.channel.typing():
            async for curr_chunk in await acompletion(**kwargs):
                if prev_chunk:
                    prev_content = prev_chunk.choices[0].delta.content or ""
                    curr_content = curr_chunk.choices[0].delta.content or ""
                    if not response_msgs or len(response_contents[-1] + prev_content) > EMBED_MAX_LENGTH:
                        reply_to_msg = new_msg if not response_msgs else response_msgs[-1]
                        embed = discord.Embed(description="⏳", color=EMBED_COLOR_INCOMPLETE)
                        for warning in sorted(user_warnings):
                            embed.add_field(name=warning, value="", inline=False)
                        response_msgs += [
                            await reply_to_msg.reply(
                                embed=embed,
                                silent=True,
                            )
                        ]
                        await msg_nodes.setdefault(response_msgs[-1].id, MsgNode()).lock.acquire()
                        last_task_time = dt.now().timestamp()
                        response_contents += [""]

                    response_contents[-1] += prev_content
                    is_final_edit: bool = curr_chunk.choices[0].finish_reason != None or len(response_contents[-1] + curr_content) > EMBED_MAX_LENGTH
                    if is_final_edit or (not edit_task or edit_task.done()) and dt.now().timestamp() - last_task_time >= EDIT_DELAY_SECONDS:
                        while edit_task and not edit_task.done():
                            await asyncio.sleep(0)
                        embed.description = response_contents[-1]
                        embed.color = EMBED_COLOR_COMPLETE if is_final_edit else EMBED_COLOR_INCOMPLETE
                        edit_task = asyncio.create_task(response_msgs[-1].edit(embed=embed))
                        last_task_time = dt.now().timestamp()

                prev_chunk = curr_chunk
    except:
        logging.exception("Error while streaming response")

    # Create MsgNode data for response messages
    data = {
        "content": "".join(response_contents),
        "role": "assistant",
    }
    if LLM_ACCEPTS_NAMES:
        data["name"] = str(bot.user.id)

    for msg in response_msgs:
        msg_nodes[msg.id].data = data
        msg_nodes[msg.id].next_msg = new_msg
        msg_nodes[msg.id].lock.release()

    # Delete MsgNodes for oldest messages (lowest IDs)
    if (num_nodes := len(msg_nodes)) > MAX_MESSAGE_NODES:
        for msg_id in sorted(msg_nodes.keys())[: num_nodes - MAX_MESSAGE_NODES]:
            async with msg_nodes.setdefault(msg_id, MsgNode()).lock:
                del msg_nodes[msg_id]


async def main():
    await bot.start(config["bot_token"])


asyncio.run(main())
