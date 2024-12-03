from typing import Callable, Dict, List
import openai
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
import os
import instructor
from pydantic import BaseModel, Field
from typing import Literal, Type

load_dotenv()

client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
istr_client = instructor.from_openai(client)


class ProductSearchQuery(BaseModel):
    query: str


class ProductSearchResult(BaseModel):
    analysis: str
    answer: str


class Reply(BaseModel):
    message: str


class Action(BaseModel):
    analysis: str
    action: Literal['product_search', 'reply']
    action_input: ProductSearchQuery | Reply


class ReplyAction(Action):
    action: Literal['reply']
    action_input: Reply


def get_chat_history_as_str(bot_name: str, chat_histories: List[Dict], ) -> str:
    if not chat_histories:
        return f"No messages found between user and {bot_name}"

    result = []
    for msg in chat_histories:
        sender = bot_name if msg['is_from_bot'] else "User"
        result.append(f"{sender}: {msg['message']}")
        result.append(f"Time: {msg['timestamp']}")
        result.append("-" * 30)
    return "\n".join(result)


async def act(
        prompt: str,
        chat_history_str: str,
        product_search_result: ProductSearchResult = None,
        action_type: Type[BaseModel] = Action
) -> Action | ReplyAction:
    content = prompt.format(
        chat_history=chat_history_str,
        product_search_result=product_search_result.answer if product_search_result else 'N/A')
    return await istr_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        response_model=action_type
    )


async def product_search(product_catalog: str, query: str) -> ProductSearchResult:
    return await istr_client.product_search.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Be a helpful assistant with the query"},
            {"role": "system", "content": product_catalog},
            {"role": "user", "content": query}],
        response_model=ProductSearchResult
    )


async def reply(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        chat_histories: List[Dict],
        config: Dict,
) -> str:
    if update.message and update.message.text:
        chat_histories_str = get_chat_history_as_str(config['name'], chat_histories)
        prompt = config.get('prompt', 'Be a helpful assistant with the query, {chat_history}')
        action = await act(prompt, chat_histories_str)
        if action.action == 'product_search':
            product_search_result = await product_search(config['product_catalog'], action.action_input.query)
            action = await act(update.message.text, chat_histories_str, product_search_result, ReplyAction)
        assert action.action == 'reply'
        return action.action_input.message

    return "Sorry, I can only echo text messages."


async def echo_reply(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        chat_histories: List[Dict],
        config: Dict,
) -> str:
    """
    Simple echo reply function that returns the received message.

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_histories: List of previous chat messages

    Returns:
        String response to be sent back to the user
    """
    if update.message and update.message.text:
        return f"Echo: {update.message.text}"
    return "Sorry, I can only echo text messages."


class ReplyFunctionFactory:
    @staticmethod
    def create_reply_function(config: Dict, bot_id: str) -> Callable:
        """
        Creates a reply function based on the provided configuration and bot_id.
        For now, it returns a simple echo function.
        
        Args:
            config: Dictionary containing bot configuration
            bot_id: Unique identifier for the bot
            
        Returns:
            Callable that takes Update, Context, and chat histories and returns a response string
        """

        async def reply_fn(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_histories: List[Dict]) -> str:
            return await reply(update, context, chat_histories, config)

        return reply_fn


if __name__ == '__main__':
    config = {
        'name': 'John Doe',
        'prompt': open('sample_prompt.txt').read(),
        'product_catalog': open('sample_product_catalog.txt').read()
    }
    # await act(config['prompt'], 'User: 你好')
    reply_fn = ReplyFunctionFactory().create_reply_function(config, '123')
    # await reply_fn(Update, ContextTypes.DEFAULT_TYPE, [])
