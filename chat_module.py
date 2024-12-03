from typing import Callable, Dict, List

from telegram import Update
from telegram.ext import ContextTypes


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
        async def echo_reply(
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            chat_histories: List[Dict]
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
            
        return echo_reply
