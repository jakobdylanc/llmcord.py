import asyncio
import base64
from dataclasses import dataclass, field
from datetime import datetime as dt
import json
import logging
import requests
from typing import Optional

import discord
from openai import AsyncOpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

with open("config.json", "r") as file:
    config = {k: v for d in json.load(file).values() for k, v in d.items()}

LLM_ACCEPTS_IMAGES: bool = any(x in config["model"] for x in ("gpt-4o", "claude-3", "gemini", "pixtral", "llava", "vision"))
LLM_ACCEPTS_NAMES: bool = "openai/" in config["model"]

ALLOWED_FILE_TYPES = ("image", "text")
ALLOWED_CHANNEL_TYPES = (discord.ChannelType.text, discord.ChannelType.public_thread, discord.ChannelType.private_thread, discord.ChannelType.private)
ALLOWED_CHANNEL_IDS = config["allowed_channel_ids"]
ALLOWED_ROLE_IDS = config["allowed_role_ids"]

MAX_TEXT = config["max_text"]
MAX_IMAGES = config["max_images"] if LLM_ACCEPTS_IMAGES else 0
MAX_MESSAGES = config["max_messages"]

STREAMING_INDICATOR = " ⚪"
EDIT_DELAY_SECONDS = 1

USE_PLAIN_RESPONSES: bool = config["use_plain_responses"]
MAX_MESSAGE_LENGTH = 2000 if USE_PLAIN_RESPONSES else (4096 - len(STREAMING_INDICATOR))

EMBED_COLOR_COMPLETE = discord.Color.dark_green()
EMBED_COLOR_INCOMPLETE = discord.Color.orange()

MAX_MESSAGE_NODES = 100

provider, model = config["model"].split("/", 1)
base_url = config["providers"][provider]["base_url"]
api_key = config["providers"][provider].get("api_key", "None")
openai_client = AsyncOpenAI(base_url=base_url, api_key=api_key)

intents = discord.Intents.default()
intents.message_content = True
activity = discord.CustomActivity(name=config["status_message"][:128] or "github.com/jakobdylanc/llmcord.py")
discord_client = discord.Client(intents=intents, activity=activity)

msg_nodes = {}
last_task_time = None

if config["client_id"] != 123456789:
    print(f"\nBOT INVITE URL:\nhttps://discord.com/api/oauth2/authorize?client_id={config['client_id']}&permissions=412317273088&scope=bot\n")


@dataclass
class MsgNode:
    name: str = ""
    role: str = ""
    text: str = ""
    images: list = field(default_factory=list)

    next_msg: Optional[discord.Message] = None

    has_bad_attachments: bool = False
    fetch_next_failed: bool = False

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@discord_client.event
async def on_message(new_msg):
    global msg_nodes, last_task_time

    # Filter out unwanted messages
    if (
        new_msg.channel.type not in ALLOWED_CHANNEL_TYPES
        or (new_msg.channel.type != discord.ChannelType.private and discord_client.user not in new_msg.mentions)
        or (ALLOWED_CHANNEL_IDS and not any(id in ALLOWED_CHANNEL_IDS for id in (new_msg.channel.id, getattr(new_msg.channel, "parent_id", None))))
        or (ALLOWED_ROLE_IDS and (new_msg.channel.type == discord.ChannelType.private or not any(role.id in ALLOWED_ROLE_IDS for role in new_msg.author.roles)))
        or new_msg.author.bot
    ):
        return

    # Build message chain and set user warnings
    messages = []
    user_warnings = set()
    curr_msg = new_msg
    while curr_msg and len(messages) < MAX_MESSAGES:
        curr_node = msg_nodes.setdefault(curr_msg.id, MsgNode())

        async with curr_node.lock:
            if not curr_node.name:
                good_attachments = {type: [att for att in curr_msg.attachments if att.content_type and type in att.content_type] for type in ALLOWED_FILE_TYPES}

                curr_node.name = str(curr_msg.author.id)

                curr_node.role = "assistant" if curr_msg.author == discord_client.user else "user"

                curr_node.text = "\n".join(
                    ([curr_msg.content] if curr_msg.content else [])
                    + [embed.description for embed in curr_msg.embeds if embed.description]
                    + [requests.get(att.url).text for att in good_attachments["text"]]
                )
                if curr_node.text.startswith(discord_client.user.mention):
                    curr_node.text = curr_node.text.replace(discord_client.user.mention, "", 1).lstrip()

                curr_node.images = [
                    dict(type="image_url", image_url=dict(url=f"data:{att.content_type};base64,{base64.b64encode(requests.get(att.url).content).decode('utf-8')}"))
                    for att in good_attachments["image"]
                ]

                curr_node.has_bad_attachments = len(curr_msg.attachments) > sum(len(att_list) for att_list in good_attachments.values())

                try:
                    if (
                        not curr_msg.reference
                        and curr_msg.channel.type != discord.ChannelType.private
                        and discord_client.user.mention not in curr_msg.content
                        and (prev_msg_in_channel := ([m async for m in curr_msg.channel.history(before=curr_msg, limit=1)] or [None])[0])
                        and any(prev_msg_in_channel.type == type for type in (discord.MessageType.default, discord.MessageType.reply))
                        and prev_msg_in_channel.author == curr_msg.author
                    ):
                        curr_node.next_msg = prev_msg_in_channel
                    else:
                        next_is_thread_parent: bool = not curr_msg.reference and curr_msg.channel.type == discord.ChannelType.public_thread
                        if next_msg_id := curr_msg.channel.id if next_is_thread_parent else getattr(curr_msg.reference, "message_id", None):
                            next_node = msg_nodes.setdefault(next_msg_id, MsgNode())
                            while next_node.lock.locked():
                                await asyncio.sleep(0)
                            curr_node.next_msg = (
                                (curr_msg.channel.starter_message or await curr_msg.channel.parent.fetch_message(next_msg_id))
                                if next_is_thread_parent
                                else (curr_msg.reference.cached_message or await curr_msg.channel.fetch_message(next_msg_id))
                            )
                except (discord.NotFound, discord.HTTPException, AttributeError):
                    logging.exception("Error fetching next message in the chain")
                    curr_node.fetch_next_failed = True

            if curr_node.text[:MAX_TEXT] or curr_node.images[:MAX_IMAGES]:
                if LLM_ACCEPTS_IMAGES:
                    content = ([dict(type="text", text=curr_node.text[:MAX_TEXT])] if curr_node.text[:MAX_TEXT] else []) + curr_node.images[:MAX_IMAGES]
                else:
                    content = curr_node.text[:MAX_TEXT]

                message = dict(role=curr_node.role, content=content)
                if LLM_ACCEPTS_NAMES:
                    message["name"] = curr_node.name

                messages.append(message)

            if curr_node.text > curr_node.text[:MAX_TEXT]:
                user_warnings.add(f"⚠️ Max {MAX_TEXT:,} characters per message")
            if curr_node.images > curr_node.images[:MAX_IMAGES]:
                user_warnings.add(f"⚠️ Max {MAX_IMAGES} image{'' if MAX_IMAGES == 1 else 's'} per message" if MAX_IMAGES > 0 else "⚠️ Can't see images")
            if curr_node.has_bad_attachments:
                user_warnings.add("⚠️ Unsupported attachments")
            if curr_node.fetch_next_failed or (curr_node.next_msg and len(messages) == MAX_MESSAGES):
                user_warnings.add(f"⚠️ Only using last {len(messages)} message{'' if len(messages) == 1 else 's'}")

            curr_msg = curr_node.next_msg

    logging.info(f"Message received (user ID: {new_msg.author.id}, attachments: {len(new_msg.attachments)}, conversation length: {len(messages)}):\n{new_msg.content}")

    if config["system_prompt"]:
        system_prompt_extras = [f"Today's date: {dt.now().strftime('%B %d %Y')}."]
        if LLM_ACCEPTS_NAMES:
            system_prompt_extras.append("User's names are their Discord IDs and should be typed as '<@ID>'.")

        messages.append(dict(role="system", content="\n".join([config["system_prompt"]] + system_prompt_extras)))

    # Generate and send response message(s) (can be multiple if response is long)
    response_msgs = []
    response_contents = []
    prev_chunk = None
    edit_task = None

    kwargs = dict(model=model, messages=messages[::-1], stream=True, extra_body=config["extra_api_parameters"])
    try:
        async with new_msg.channel.typing():
            async for curr_chunk in await openai_client.chat.completions.create(**kwargs):
                if prev_chunk:
                    prev_content = prev_chunk.choices[0].delta.content or ""
                    curr_content = curr_chunk.choices[0].delta.content or ""

                    if response_contents or prev_content:
                        if not response_contents or len(response_contents[-1] + prev_content) > MAX_MESSAGE_LENGTH:
                            response_contents.append("")

                            if not USE_PLAIN_RESPONSES:
                                reply_to_msg = new_msg if not response_msgs else response_msgs[-1]
                                embed = discord.Embed(description=(prev_content + STREAMING_INDICATOR), color=EMBED_COLOR_INCOMPLETE)
                                for warning in sorted(user_warnings):
                                    embed.add_field(name=warning, value="", inline=False)
                                response_msg = await reply_to_msg.reply(embed=embed, silent=True)
                                msg_nodes[response_msg.id] = MsgNode(next_msg=new_msg)
                                await msg_nodes[response_msg.id].lock.acquire()
                                last_task_time = dt.now().timestamp()
                                response_msgs.append(response_msg)

                        response_contents[-1] += prev_content

                        if not USE_PLAIN_RESPONSES:
                            msg_split_incoming: bool = len(response_contents[-1] + curr_content) > MAX_MESSAGE_LENGTH
                            is_final_edit: bool = msg_split_incoming or (finish_reason := curr_chunk.choices[0].finish_reason) != None

                            if is_final_edit or ((not edit_task or edit_task.done()) and dt.now().timestamp() - last_task_time >= EDIT_DELAY_SECONDS):
                                while edit_task and not edit_task.done():
                                    await asyncio.sleep(0)
                                embed.description = response_contents[-1] if is_final_edit else (response_contents[-1] + STREAMING_INDICATOR)
                                embed.color = EMBED_COLOR_COMPLETE if msg_split_incoming or finish_reason == "stop" else EMBED_COLOR_INCOMPLETE
                                edit_task = asyncio.create_task(response_msgs[-1].edit(embed=embed))
                                last_task_time = dt.now().timestamp()

                prev_chunk = curr_chunk

        if USE_PLAIN_RESPONSES:
            for content in response_contents:
                reply_to_msg = new_msg if not response_msgs else response_msgs[-1]
                response_msg = await reply_to_msg.reply(content=content)
                msg_nodes[response_msg.id] = MsgNode(next_msg=new_msg)
                await msg_nodes[response_msg.id].lock.acquire()
                response_msgs.append(response_msg)
    except:
        logging.exception("Error while generating response")

    # Create MsgNode data for response messages
    for msg in response_msgs:
        msg_nodes[msg.id].name = str(discord_client.user.id)
        msg_nodes[msg.id].role = "assistant"
        msg_nodes[msg.id].text = "".join(response_contents)

        msg_nodes[msg.id].lock.release()

    # Delete oldest MsgNodes (lowest message IDs) from the cache
    if (num_nodes := len(msg_nodes)) > MAX_MESSAGE_NODES:
        for msg_id in sorted(msg_nodes.keys())[: num_nodes - MAX_MESSAGE_NODES]:
            async with msg_nodes.setdefault(msg_id, MsgNode()).lock:
                del msg_nodes[msg_id]


async def main():
    await discord_client.start(config["bot_token"])


asyncio.run(main())
