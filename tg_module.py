import uuid
from typing import Dict, List, Optional

from loguru import logger
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from chat_module import ReplyFunctionFactory
from database import Database


class TelegramBotManager:
    def __init__(self, database: Database):
        self.db = database
        self.running_bots: Dict[str, Application] = {}
        logger.info("TelegramBotManager initialized")

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
        logger.info(f"Creating new bot with ID: {bot_id}")
        if self.db.add_bot(bot_id, token, config):
            logger.success(f"Bot {bot_id} created successfully")
            return bot_id
        logger.error(f"Failed to create bot {bot_id}")
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
            logger.warning(f"Cannot update bot {bot_id} while it is running")
            return False
        logger.info(f"Updating configuration for bot {bot_id}")
        success = self.db.update_bot(bot_id, config)
        if success:
            logger.success(f"Bot {bot_id} configuration updated successfully")
        else:
            logger.error(f"Failed to update bot {bot_id} configuration")
        return success

    async def delete_bot(self, bot_id: str) -> bool:
        """
        Delete a bot and its chat history.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Attempting to delete bot {bot_id}")
        if bot_id in self.running_bots:
            logger.info(f"Stopping bot {bot_id} before deletion")
            await self.stop_bot(bot_id)
        success = self.db.delete_bot(bot_id)
        if success:
            logger.success(f"Bot {bot_id} deleted successfully")
        else:
            logger.error(f"Failed to delete bot {bot_id}")
        return success

    async def start_bot(self, bot_id: str) -> bool:
        """
        Start running a bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting bot {bot_id}")
        
        if bot_id in self.running_bots:
            logger.warning(f"Bot {bot_id} is already running")
            return False

        bot_data = self.db.get_bot(bot_id)
        if not bot_data:
            logger.error(f"Bot {bot_id} not found in database")
            return False

        try:
            application = Application.builder().token(bot_data["token"]).build()
            reply_func = ReplyFunctionFactory.create_reply_function(bot_data["config"], bot_id)
            logger.debug(f"Created application and reply function for bot {bot_id}")

            async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if not update.effective_chat:
                    logger.warning("Received update without effective chat")
                    return

                chat_id = str(update.effective_chat.id)
                chat_name = update.effective_chat.title or update.effective_chat.first_name or str(chat_id)
                
                logger.debug(f"Processing message from chat {chat_id} ({chat_name})")
                
                # Ensure chat exists in database
                self.db.add_chat(chat_id, bot_id, chat_name)
                
                # Get chat history
                chat_history = self.db.get_chat_history(chat_id, bot_id)
                
                # Record incoming message
                if update.message and update.message.text:
                    logger.debug(f"Recording incoming message from chat {chat_id}")
                    self.db.add_message(chat_id, bot_id, update.message.text, False)
                
                # Generate reply
                reply = await reply_func(update, context, chat_history)
                
                # Record and send reply
                if reply:
                    logger.debug(f"Sending reply to chat {chat_id}")
                    self.db.add_message(chat_id, bot_id, reply, True)
                    await update.message.reply_text(reply)

            # Add handlers
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
            logger.debug(f"Added message handler for bot {bot_id}")
            
            # Start the bot
            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            self.running_bots[bot_id] = application
            self.db.update_bot_status(bot_id, "running")
            logger.success(f"Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error starting bot {bot_id}: {str(e)}")
            return False

    async def stop_bot(self, bot_id: str) -> bool:
        """
        Stop a running bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Stopping bot {bot_id}")
        
        if bot_id not in self.running_bots:
            logger.warning(f"Bot {bot_id} is not running")
            return False

        try:
            application = self.running_bots[bot_id]
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            
            del self.running_bots[bot_id]
            self.db.update_bot_status(bot_id, "stopped")
            logger.success(f"Bot {bot_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Error stopping bot {bot_id}: {str(e)}")
            return False

    def list_bots(self) -> List[Dict]:
        """
        Get a list of all bots and their status.
        
        Returns:
            List of dictionaries containing bot information
        """
        logger.debug("Retrieving list of all bots")
        return self.db.get_all_bots()

    def list_chats(self, bot_id: str) -> List[Dict]:
        """
        Get a list of all chats for a specific bot.
        
        Args:
            bot_id: Unique identifier for the bot
            
        Returns:
            List of dictionaries containing chat information
        """
        logger.debug(f"Retrieving chat list for bot {bot_id}")
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
        logger.debug(f"Retrieving chat history for bot {bot_id}, chat {chat_id}")
        return self.db.get_chat_history(chat_id, bot_id)
