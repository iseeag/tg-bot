import os
from traceback import format_exc
from typing import Callable, Dict, List, Literal, Type

import instructor
import openai
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field
from telegram import Update
from telegram.ext import ContextTypes

load_dotenv()

client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
istr_client = instructor.from_openai(client)

logger.info("OpenAI client initialized with base URL: {}", os.getenv("OPENAI_BASE_URL"))


class ProductSearchQuery(BaseModel):
    query: str = Field(..., title="A fully contextualized product search query sentence")


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


def get_chat_history_as_str(
        bot_name: str,
        chat_histories: List[Dict],
        last_user_msg: str = None
) -> str:
    if not chat_histories:
        return f"No messages found between user and {bot_name}"

    result = []
    for msg in chat_histories:
        sender = bot_name if msg['is_from_bot'] else "User"
        result.append(f"{sender}: {msg['message']}")
        result.append(f"Time: {msg['timestamp']}")
        result.append("-" * 30)
    if last_user_msg:
        result.append(f"User: {last_user_msg}")
        result.append(f"Time: Just now")
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

    logger.debug("Generating action with prompt: {}", content[:100] + "..." if len(content) > 100 else content)
    try:
        action = await istr_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            response_model=action_type
        )
        logger.debug(f"Generated action: {action}")
        return action
    except Exception as e:
        logger.exception(f"Error generating action: {str(e)}, {format_exc()}")
        raise e


async def product_search(product_catalog: str, query: str) -> ProductSearchResult:
    logger.info("Performing product search with query: {}", query)
    try:
        result = await istr_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Be a helpful assistant with the query"},
                {"role": "system", "content": product_catalog},
                {"role": "user", "content": query}],
            response_model=ProductSearchResult
        )
        logger.debug(f"Product search result: {result}")
        return result
    except Exception as e:
        logger.exception(f"Error in product search: {str(e)}, {format_exc()}")
        raise e


async def reply(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        chat_histories: List[Dict],
        config: Dict,
) -> str:
    if update.message and update.message.text:
        logger.info("Processing message: {}",
                    update.message.text[:100] + "..." if len(update.message.text) > 100 else update.message.text)

        chat_histories_str = get_chat_history_as_str(config['name'], chat_histories, update.message.text)
        logger.debug("Chat history: {}", chat_histories_str)
        prompt = config.get('prompt', 'Be a helpful assistant with the query, {chat_history}')

        try:
            action = await act(prompt, chat_histories_str)

            if action.action == 'product_search':
                logger.info("Initiating product search flow")
                product_search_result = await product_search(config['product_catalog'], action.action_input.query)
                action = await act(prompt, chat_histories_str, product_search_result, ReplyAction)
                logger.debug("Generated reply after product search")

            assert action.action == 'reply'
            return action.action_input.message

        except Exception as e:
            logger.exception(f"Error processing reply: {str(e)}, {format_exc()}")
            return "Sorry, I encountered an error while processing your message."

    logger.warning("Received non-text message")
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
        logger.debug("Echo reply for message: {}", update.message.text)
        return f"Echo: {update.message.text}"
    logger.warning("Received non-text message in echo reply")
    return "Sorry, I can only echo text messages."


class ReplyFunctionFactory:
    @staticmethod
    def create_reply_function(config: Dict, bot_id: str) -> Callable:
        """
        Creates a reply function based on the provided configuration and bot_id.
        
        Args:
            config: Dictionary containing bot configuration
            bot_id: Unique identifier for the bot
            
        Returns:
            Callable that takes Update, Context, and chat histories and returns a response string
        """
        logger.info("Creating reply function for bot {} with config: {}", bot_id, config)

        async def reply_fn(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_histories: List[Dict]) -> str:
            return await reply(update, context, chat_histories, config)

        return reply_fn


if __name__ == '__main__':
    logger.info("Running chat_module in standalone mode")
    config = {
        'name': 'John Doe',
        'prompt': open('sample_prompt.txt').read(),
        'product_catalog': open('sample_product_catalog.txt').read()
    }
    logger.debug("Loaded configuration: {}", config)
    # await act(config['prompt'], 'User: 你好')
    reply_fn = ReplyFunctionFactory().create_reply_function(config, '123')
    # await reply_fn(Update, ContextTypes.DEFAULT_TYPE, [])
