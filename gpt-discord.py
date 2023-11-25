import asyncio
import logging
import os
import time
import dotenv
import discord
import openai
import tiktoken


dotenv.load_dotenv()
os.environ["GPT_MODEL"] = (
    os.environ["GPT_MODEL"]
    .replace("gpt-3.5-turbo", "gpt-3.5-turbo-1106", 1)
    .replace("gpt-4-turbo-vision", "gpt-4-vision-preview", 1)
    .replace("gpt-4-turbo", "gpt-4-1106-preview", 1)
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

openai_client = openai.AsyncOpenAI()
encoding = tiktoken.get_encoding("cl100k_base")
SYSTEM_PROMPT = {
    "role": "system",
    "content": f"{os.environ['CUSTOM_SYSTEM_PROMPT']}\nUser's names are their Discord IDs and should be typed as '<@ID>'.",
}
EXTRA_TOKENS_PER = {"image_url": 85, "message": 3, "name": 1, "reply": 3}
MAX_TOTAL_TOKENS = {
    "gpt-3.5-turbo-1106": 16385,
    "gpt-4-1106-preview": 128000,
    "gpt-4-vision-preview": 128000,
}
MAX_COMPLETION_TOKENS = 1024

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)
msg_nodes = {}
in_progress_message_ids = []
EMBED_COLOR = {"incomplete": discord.Color.orange(), "complete": discord.Color.green()}
EMBED_MAX_LENGTH = 4096
EDITS_PER_SECOND = 1.3


def count_tokens(msg, num_tokens=EXTRA_TOKENS_PER["message"]):
    for key, value in msg.items():
        if key == "content" and isinstance(value, list):
            for item in value:
                num_tokens += count_tokens(item, num_tokens=0)
        elif key not in ("image_url", "type"):
            num_tokens += len(encoding.encode(value))
        if key in EXTRA_TOKENS_PER:
            num_tokens += EXTRA_TOKENS_PER[key]
    return num_tokens


MAX_PROMPT_TOKENS_ADJUSTED = (
    MAX_TOTAL_TOKENS[os.environ["GPT_MODEL"]]
    - MAX_COMPLETION_TOKENS
    - EXTRA_TOKENS_PER["reply"]
    - count_tokens(SYSTEM_PROMPT)
)


class MsgNode:
    def __init__(self, msg, reference_node=None):
        self.msg = msg
        self.tokens = count_tokens(msg)
        self.reference_node = reference_node

    def get_reference_chain(self, max_tokens=MAX_PROMPT_TOKENS_ADJUSTED):
        msgs = []
        num_tokens = 0
        current_node = self
        while current_node is not None:
            num_tokens += current_node.tokens
            if num_tokens > max_tokens:
                break
            msgs += [current_node.msg]
            current_node = current_node.reference_node
        return msgs[::-1]


@discord_client.event
async def on_message(message):
    # Filter out messages we don't want
    if (
        message.channel.type != discord.ChannelType.private
        and discord_client.user not in message.mentions
    ) or message.author.bot:
        return

    # If user replied to a message that's still generating, wait until it's done
    while message.reference and message.reference.message_id in in_progress_message_ids:
        await asyncio.sleep(0)

    async with message.channel.typing():
        # Loop through message reply chain and create MsgNodes
        current_msg = message
        previous_msg_id = None
        while True:
            current_msg_text = (
                current_msg.embeds[0].description
                if current_msg.author == discord_client.user
                else current_msg.content
            )
            if current_msg_text.startswith(discord_client.user.mention):
                current_msg_text = current_msg_text[
                    len(discord_client.user.mention) :
                ].lstrip()
            current_msg_content = (
                [{"type": "text", "text": current_msg_text}] if current_msg_text else []
            )
            if os.environ["GPT_MODEL"] == "gpt-4-vision-preview":
                current_msg_content += [
                    {
                        "type": "image_url",
                        "image_url": {"url": att.url, "detail": "low"},
                    }
                    for att in current_msg.attachments
                    if "image" in att.content_type
                ]
            current_msg_author_role = (
                "assistant" if current_msg.author == discord_client.user else "user"
            )
            msg_nodes[current_msg.id] = MsgNode(
                {
                    "role": current_msg_author_role,
                    "content": current_msg_content,
                    "name": str(current_msg.author.id),
                }
            )
            if previous_msg_id:
                msg_nodes[previous_msg_id].reference_node = msg_nodes[current_msg.id]
            if not current_msg.reference:
                break
            if current_msg.reference.message_id in msg_nodes:
                msg_nodes[current_msg.id].reference_node = msg_nodes[
                    current_msg.reference.message_id
                ]
                break
            previous_msg_id = current_msg.id
            try:
                current_msg = (
                    current_msg.reference.resolved
                    if isinstance(current_msg.reference.resolved, discord.Message)
                    else await message.channel.fetch_message(
                        current_msg.reference.message_id
                    )
                )
            except (discord.NotFound, discord.HTTPException):
                break

        # Build conversation history from reply chain
        msgs = [SYSTEM_PROMPT] + msg_nodes[message.id].get_reference_chain()

        # Generate and send bot reply
        logging.info("Generating response for content: %s", msgs[-1])
        response_messages = []
        response_message_contents = []
        previous_content = None
        edit_message_task = None
        async for part in await openai_client.chat.completions.create(
            model=os.environ["GPT_MODEL"],
            messages=msgs,
            max_tokens=MAX_COMPLETION_TOKENS,
            stream=True,
        ):
            current_content = part.choices[0].delta.content or ""
            if previous_content:
                if (
                    not response_messages
                    or len(response_message_contents[-1] + previous_content)
                    > EMBED_MAX_LENGTH
                ):
                    reply_message = (
                        message if not response_messages else response_messages[-1]
                    )
                    embed_color = (
                        EMBED_COLOR["complete"]
                        if current_content == ""
                        else EMBED_COLOR["incomplete"]
                    )
                    response_messages += [
                        await reply_message.reply(
                            embed=discord.Embed(
                                description=previous_content, color=embed_color
                            ),
                            silent=True,
                        )
                    ]
                    in_progress_message_ids.append(response_messages[-1].id)
                    last_message_task_time = time.time()
                    response_message_contents += [""]
                response_message_contents[-1] += previous_content
                if response_message_contents[-1] != previous_content:
                    final_message_edit = (
                        len(response_message_contents[-1] + current_content)
                        > EMBED_MAX_LENGTH
                        or current_content == ""
                    )
                    if (
                        final_message_edit
                        or (not edit_message_task or edit_message_task.done())
                        and time.time() - last_message_task_time
                        >= len(in_progress_message_ids) / EDITS_PER_SECOND
                    ):
                        while edit_message_task and not edit_message_task.done():
                            await asyncio.sleep(0)
                        embed_color = (
                            EMBED_COLOR["complete"]
                            if final_message_edit
                            else EMBED_COLOR["incomplete"]
                        )
                        edit_message_task = asyncio.create_task(
                            response_messages[-1].edit(
                                embed=discord.Embed(
                                    description=response_message_contents[-1],
                                    color=embed_color,
                                )
                            )
                        )
                        last_message_task_time = time.time()
            previous_content = current_content

        # Create MsgNode(s) for bot reply message(s) (can be multiple if bot reply was long)
        for response_message in response_messages:
            msg_nodes[response_message.id] = MsgNode(
                {
                    "role": "assistant",
                    "content": "".join(response_message_contents),
                    "name": str(discord_client.user.id),
                },
                reference_node=msg_nodes[message.id],
            )
            in_progress_message_ids.remove(response_message.id)


async def main():
    await discord_client.start(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
