import uuid
from typing import Dict, List, Optional

from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from chat_module import ReplyFunctionFactory
from database import Database


class TelegramBotManager:
    def __init__(self, database: Database):
        self.db = database
        self.running_bots: Dict[str, Application] = {}

    def create_bot(self, token: str, config: Dict) -> Optional[str]:
        """
        Create a new bot with the given token and configuration.
        
        Args:
            token: Telegram bot token
            config: Dictionary containing bot configuration
            
        Returns:
            bot_id if successful, None otherwise
        """
        bot_id = str(uuid.uuid4())
        if self.db.add_bot(bot_id, token, config):
            return bot_id
        return None

    def update_bot(self, bot_id: str, config: Dict) -> bool:
        """
        Update the configuration of an existing bot.
        
        Args:
            bot_id: Unique identifier for the bot
            config: New configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id in self.running_bots:
            return False
        return self.db.update_bot(bot_id, config)

    async def delete_bot(self, bot_id: str) -> bool:
        """
        Delete a bot and its chat history.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id in self.running_bots:
            await self.stop_bot(bot_id)
        return self.db.delete_bot(bot_id)

    async def start_bot(self, bot_id: str) -> bool:
        """
        Start running a bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id in self.running_bots:
            return False

        bot_data = self.db.get_bot(bot_id)
        if not bot_data:
            return False

        application = Application.builder().token(bot_data["token"]).build()
        reply_func = ReplyFunctionFactory.create_reply_function(bot_data["config"], bot_id)

        async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.effective_chat:
                return

            chat_id = str(update.effective_chat.id)
            chat_name = update.effective_chat.title or update.effective_chat.first_name or str(chat_id)
            
            # Ensure chat exists in database
            self.db.add_chat(chat_id, bot_id, chat_name)
            
            # Get chat history
            chat_history = self.db.get_chat_history(chat_id, bot_id)
            
            # Record incoming message
            if update.message and update.message.text:
                self.db.add_message(chat_id, bot_id, update.message.text, False)
            
            # Generate reply
            reply = await reply_func(update, context, chat_history)
            
            # Record and send reply
            if reply:
                self.db.add_message(chat_id, bot_id, reply, True)
                await update.message.reply_text(reply)

        # Add handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        # Start the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        self.running_bots[bot_id] = application
        self.db.update_bot_status(bot_id, "running")
        return True

    async def stop_bot(self, bot_id: str) -> bool:
        """
        Stop a running bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        if bot_id not in self.running_bots:
            return False

        application = self.running_bots[bot_id]
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        
        del self.running_bots[bot_id]
        self.db.update_bot_status(bot_id, "stopped")
        return True

    def list_bots(self) -> List[Dict]:
        """
        Get a list of all bots and their status.
        
        Returns:
            List of dictionaries containing bot information
        """
        return self.db.get_all_bots()

    def list_chats(self, bot_id: str) -> List[Dict]:
        """
        Get a list of all chats for a specific bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            List of dictionaries containing chat information
        """
        return self.db.get_chats(bot_id)

    def get_chat_history(self, bot_id: str, chat_id: str) -> List[Dict]:
        """
        Get the chat history for a specific chat.
        
        Args:
            bot_id: Unique identifier for the bot
            chat_id: Unique identifier for the chat
            
        Returns:
            List of dictionaries containing message information
        """
        return self.db.get_chat_history(chat_id, bot_id)
