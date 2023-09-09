import openai, tiktoken, discord, asyncio, os, time
from dotenv import load_dotenv; load_dotenv()
os.environ["EDITS_PER_SECOND"] = str(max(float(os.environ["EDITS_PER_SECOND"]), 1))
openai.api_key = os.environ["OPENAI_API_KEY"]
encoding = tiktoken.get_encoding("cl100k_base")
SYSTEM_PROMPT = {"role": "system", "content": f"{os.environ['CUSTOM_SYSTEM_PROMPT']}\nUser's names are their Discord IDs and should be typed as '<@ID>'. Knowledge cutoff: Sep 2021."}
EXTRA_TOKENS_PER = {"message": 3, "name": 1, "reply": 3}
MAX_TOTAL_TOKENS = {"gpt-4": 8192, "gpt-4-32k": 32768, "gpt-3.5-turbo": 4096, "gpt-3.5-turbo-16k": 16384}
MAX_COMPLETION_TOKENS = 1024
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
msg_nodes = {}
in_progress_message_ids = []
EMBED_MAX_LENGTH = 4096
EMBED_COLOR = {"incomplete": discord.Color.orange(), "complete": discord.Color.green()}


async def chat_completion_stream(msgs):
    async for chunk in await openai.ChatCompletion.acreate(
        model=os.environ["GPT_MODEL"],
        messages=msgs,
        max_tokens=MAX_COMPLETION_TOKENS,
        stream=True,
    ):
        delta = chunk["choices"][0].get("delta", {})
        yield delta


def count_tokens(msg):
    num_tokens = EXTRA_TOKENS_PER["message"]
    for key, value in msg.items():
        num_tokens += len(encoding.encode(value))
        if key == "name": num_tokens += EXTRA_TOKENS_PER["name"]
    return num_tokens
MAX_PROMPT_TOKENS_ADJUSTED = MAX_TOTAL_TOKENS[os.environ["GPT_MODEL"]] - MAX_COMPLETION_TOKENS - EXTRA_TOKENS_PER["reply"] - count_tokens(SYSTEM_PROMPT)


class MsgNode:
    def __init__(self, msg, reference_node=None):
        self.msg = msg
        self.tokens = count_tokens(msg)
        self.reference_node = reference_node

    def get_reference_chain(self, max_tokens=MAX_PROMPT_TOKENS_ADJUSTED):
        reference_chain = []
        num_tokens = 0
        current_node = self
        while current_node != None:
            num_tokens += current_node.tokens
            if num_tokens > max_tokens: break
            reference_chain.append(current_node.msg)
            current_node = current_node.reference_node
        return reference_chain[::-1]
    

@bot.event
async def on_message(message):

    # Filter out messages we don't want
    if (message.channel.type != discord.ChannelType.private and bot.user not in message.mentions) or message.author.bot: return
    user_message_content = message.content.replace(bot.user.mention, "", 1).strip()
    if not user_message_content: return

    # If user replied to a message that's still generating, wait until it's done
    while message.reference and message.reference.message_id in in_progress_message_ids: await asyncio.sleep(0)

    print(f"Generating GPT response for prompt:\n{user_message_content}")

    async with message.channel.typing():

        # Create MsgNode for user message
        msg_nodes[message.id] = MsgNode({"role": "user", "content": user_message_content, "name": str(message.author.id)})
        
        # Loop through message reply chain and create MsgNodes
        current_msg = message
        while current_msg.reference:
            if current_msg.id in msg_nodes and current_msg.reference.message_id in msg_nodes:
                msg_nodes[current_msg.id].reference_node = msg_nodes[current_msg.reference.message_id]
                break
            else:
                try:
                    previous_msg_id = current_msg.id
                    current_msg = current_msg.reference.resolved if isinstance(current_msg.reference.resolved, discord.Message) else await message.channel.fetch_message(current_msg.reference.message_id)
                    current_msg_content = current_msg.embeds[0].description if current_msg.author == bot.user else current_msg.content
                    if not current_msg_content or current_msg.id in msg_nodes: break
                    current_msg_author_role = "assistant" if current_msg.author == bot.user else "user"
                    msg_nodes[current_msg.id] = MsgNode({"role": current_msg_author_role, "content": current_msg_content, "name": str(current_msg.author.id)})
                    msg_nodes[previous_msg_id].reference_node = msg_nodes[current_msg.id]
                except (discord.NotFound, discord.HTTPException): break
 
        # Build conversation history from reply chain
        msgs = [SYSTEM_PROMPT] + msg_nodes[message.id].get_reference_chain()

        # Generate and send bot reply
        response_messages, response_message_contents = [], []
        async for current_delta in chat_completion_stream(msgs):
            if "previous_delta" in locals():
                current_delta_content = current_delta.get("content", "")
                previous_delta_content = previous_delta.get("content", "")
                if previous_delta_content:
                    if response_messages == [] or len(response_message_contents[-1]+previous_delta_content) > EMBED_MAX_LENGTH:
                        reply_message = message if response_messages == [] else response_messages[-1]
                        embed_color = EMBED_COLOR["complete"] if current_delta == {} else EMBED_COLOR["incomplete"]
                        response_messages.append(await reply_message.reply(embed=discord.Embed(description=previous_delta_content, color=embed_color)))
                        in_progress_message_ids.append(response_messages[-1].id)
                        last_message_task_time = time.time()
                        response_message_contents.append("")
                    response_message_contents[-1] += previous_delta_content
                    
                    if response_message_contents[-1] != previous_delta_content:
                        final_message_edit = True if len(response_message_contents[-1]+current_delta_content) > EMBED_MAX_LENGTH or current_delta == {} else False
                        if final_message_edit or ("edit_message_task" not in locals() or edit_message_task.done()) and time.time()-last_message_task_time >= len(in_progress_message_ids)/float(os.environ["EDITS_PER_SECOND"]):
                            while "edit_message_task" in locals() and not edit_message_task.done(): await asyncio.sleep(0)
                            embed_color = EMBED_COLOR["complete"] if final_message_edit else EMBED_COLOR["incomplete"]
                            edit_message_task = asyncio.create_task(response_messages[-1].edit(embed=discord.Embed(description=response_message_contents[-1], color=embed_color)))
                            last_message_task_time = time.time()
            previous_delta = current_delta

        # Create MsgNode(s) for bot reply message(s) (can be multiple if bot reply was long)
        for response_message in response_messages:
            msg_nodes[response_message.id] = MsgNode({"role": "assistant", "content": ''.join(response_message_contents), "name": str(bot.user.id)}, reference_node=msg_nodes[message.id])
            in_progress_message_ids.remove(response_message.id)


async def main(): await bot.start(os.environ["DISCORD_BOT_TOKEN"])
if __name__ == "__main__": asyncio.run(main())