import asyncio
import json
import threading
from typing import Dict, List

import gradio as gr

from database import Database
from tg_module import TelegramBotManager


class TelegramBotServiceGradio:
    def __init__(self):
        self.db = Database()
        self.bot_manager = TelegramBotManager(self.db)
        
        # Start asyncio event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def create_bot(self, token: str, config_str: str) -> str:
        """Create a new bot with the given token and configuration."""
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return "Error: Invalid JSON configuration"
            
        bot_id = self.bot_manager.create_bot(token, config)
        if bot_id:
            return f"Success: Bot created with ID: {bot_id}"
        return "Error: Failed to create bot"

    def list_bots(self) -> List[Dict]:
        """Get a list of all bots and their status."""
        return self.bot_manager.list_bots()

    def format_bot_list(self) -> str:
        """Format bot list for display."""
        bots = self.list_bots()
        if not bots:
            return "No bots found"
            
        result = []
        for bot in bots:
            result.append(f"Bot ID: {bot['bot_id']}")
            result.append(f"Status: {bot['status']}")
            result.append(f"Config: {json.dumps(bot['config'], indent=2)}")
            result.append("-" * 50)
        return "\n".join(result)

    async def start_bot(self, bot_id: str) -> str:
        """Start a bot."""
        if await self.bot_manager.start_bot(bot_id):
            return f"Success: Bot {bot_id} started"
        return f"Error: Failed to start bot {bot_id}"

    async def stop_bot(self, bot_id: str) -> str:
        """Stop a bot."""
        if await self.bot_manager.stop_bot(bot_id):
            return f"Success: Bot {bot_id} stopped"
        return f"Error: Failed to stop bot {bot_id}"

    async def delete_bot(self, bot_id: str) -> str:
        """Delete a bot."""
        if await self.bot_manager.delete_bot(bot_id):
            return f"Success: Bot {bot_id} deleted"
        return f"Error: Failed to delete bot {bot_id}"

    def update_bot(self, bot_id: str, config_str: str) -> str:
        """Update bot configuration."""
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return "Error: Invalid JSON configuration"
            
        if self.bot_manager.update_bot(bot_id, config):
            return f"Success: Bot {bot_id} configuration updated"
        return f"Error: Failed to update bot configuration"

    def list_chats(self, bot_id: str) -> str:
        """List all chats for a bot."""
        chats = self.bot_manager.list_chats(bot_id)
        if not chats:
            return "No chats found"
            
        result = []
        for chat in chats:
            result.append(f"Chat ID: {chat['chat_id']}")
            result.append(f"Chat Name: {chat['chat_name']}")
            result.append("-" * 30)
        return "\n".join(result)

    def get_chat_history(self, bot_id: str, chat_id: str) -> str:
        """Get chat history."""
        history = self.bot_manager.get_chat_history(bot_id, chat_id)
        if not history:
            return "No messages found"
            
        result = []
        for msg in history:
            sender = "Bot" if msg['is_from_bot'] else "User"
            result.append(f"{sender}: {msg['message']}")
            result.append(f"Time: {msg['timestamp']}")
            result.append("-" * 30)
        return "\n".join(result)

    def create_ui(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Telegram Bot Manager") as interface:
            gr.Markdown("# Telegram Bot Manager")
            
            with gr.Tab("Create Bot"):
                with gr.Row():
                    token_input = gr.Textbox(label="Bot Token")
                    config_input = gr.Textbox(
                        label="Configuration (JSON)",
                        value='{\n    "name": "My Bot",\n    "description": "A new bot"\n}',
                        lines=5
                    )
                create_btn = gr.Button("Create Bot")
                create_output = gr.Textbox(label="Result")
                create_btn.click(
                    fn=self.create_bot,
                    inputs=[token_input, config_input],
                    outputs=create_output
                )

            with gr.Tab("Manage Bots"):
                refresh_btn = gr.Button("Refresh Bot List")
                bot_list = gr.Textbox(label="Bots", lines=10)
                refresh_btn.click(
                    fn=self.format_bot_list,
                    inputs=[],
                    outputs=bot_list
                )
                
                with gr.Row():
                    bot_id_input = gr.Textbox(label="Bot ID")
                    action_btns = gr.Group()
                    with action_btns:
                        start_btn = gr.Button("Start")
                        stop_btn = gr.Button("Stop")
                        delete_btn = gr.Button("Delete")
                
                with gr.Row():
                    config_update = gr.Textbox(
                        label="New Configuration (JSON)",
                        lines=5
                    )
                    update_btn = gr.Button("Update")
                
                action_output = gr.Textbox(label="Action Result")
                
                start_btn.click(
                    fn=lambda x: asyncio.run_coroutine_threadsafe(
                        self.start_bot(x), self.loop).result(),
                    inputs=bot_id_input,
                    outputs=action_output
                )
                
                stop_btn.click(
                    fn=lambda x: asyncio.run_coroutine_threadsafe(
                        self.stop_bot(x), self.loop).result(),
                    inputs=bot_id_input,
                    outputs=action_output
                )
                
                delete_btn.click(
                    fn=lambda x: asyncio.run_coroutine_threadsafe(
                        self.delete_bot(x), self.loop).result(),
                    inputs=bot_id_input,
                    outputs=action_output
                )
                
                update_btn.click(
                    fn=self.update_bot,
                    inputs=[bot_id_input, config_update],
                    outputs=action_output
                )

            with gr.Tab("Chat History"):
                with gr.Row():
                    chat_bot_id = gr.Textbox(label="Bot ID")
                    chat_id = gr.Textbox(label="Chat ID")
                
                list_chats_btn = gr.Button("List Chats")
                chats_output = gr.Textbox(label="Chats", lines=5)
                
                view_history_btn = gr.Button("View Chat History")
                history_output = gr.Textbox(label="Chat History", lines=10)
                
                list_chats_btn.click(
                    fn=self.list_chats,
                    inputs=chat_bot_id,
                    outputs=chats_output
                )
                
                view_history_btn.click(
                    fn=self.get_chat_history,
                    inputs=[chat_bot_id, chat_id],
                    outputs=history_output
                )

        return interface

    def run(self, port: int = 7860):
        """Run the Gradio interface."""
        interface = self.create_ui()
        interface.queue()
        interface.launch(server_port=port)

if __name__ == "__main__":
    service = TelegramBotServiceGradio()
    service.run()
