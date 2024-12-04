import asyncio
import json
import threading
from typing import Dict, List, Tuple

import gradio as gr

from database import Database
from tg_module import TelegramBotManager, default_config_json


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

    def create_bot(self, token: str, bot_handle: str, config_str: str) -> str:
        """Create a new bot with the given token and configuration."""
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return "错误：JSON配置格式无效"

        bot_id = self.bot_manager.create_bot(token, bot_handle, config)
        if bot_id:
            return f"成功：机器人已创建，ID为：{bot_id}"
        return "错误：创建机器人失败"

    def list_bots(self) -> List[Dict]:
        """Get a list of all bots and their status."""
        return self.bot_manager.list_bots()

    def list_bot_handles(self) -> List[str]:
        """Get a list of all bot handles."""
        return [b['bot_handle'] for b in self.bot_manager.list_bots()]

    def get_bot_config(self, bot_handle: str) -> str:
        """Get the configuration of a bot."""
        # get_bot_by_handle
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        return json.dumps(bot['config'], indent=4, ensure_ascii=False)

    def get_bot_info(self, bot_handle: str) -> str:
        """Get the status of a bot."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        result = [f"机器人ID：{bot['bot_id']}",
                  f"用户名：{bot['bot_handle']}",
                  f"状态：{bot['status']}"]
        return "\n".join(result)

    def format_bot_list(self) -> str:
        """Format bot list for display."""
        bots = self.list_bots()
        if not bots:
            return "未找到机器人"

        result = []
        for bot in bots:
            result.append(f"机器人ID：{bot['bot_id']}")
            result.append(f"用户名：{bot['bot_handle']}")
            result.append(f"状态：{bot['status']}")
            result.append(f"配置：{json.dumps(bot['config'], indent=2, ensure_ascii=False)}")
            result.append("-" * 50)
        return "\n".join(result)

    async def start_bot(self, bot_handle: str) -> str:
        """Start a bot."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        if await self.bot_manager.start_bot(bot['bot_id']):
            return f"成功：机器人 {bot_handle} 已启动"
        return f"错误：启动机器人 {bot_handle} 失败"

    async def stop_bot(self, bot_handle: str) -> str:
        """Stop a bot."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        if await self.bot_manager.stop_bot(bot['bot_id']):
            return f"成功：机器人 {bot_handle} 已停止"
        return f"错误：停止机器人 {bot_handle} 失败"

    async def delete_bot(self, bot_handle: str) -> str:
        """Delete a bot."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        if await self.bot_manager.delete_bot(bot['bot_id']):
            return f"成功：机器人 {bot_handle} 已删除"
        return f"错误：删除机器人 {bot_handle} 失败"

    def update_bot_config(self, bot_handle: str, config_str: str) -> str:
        """Update bot configuration."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return "错误：JSON配置格式无效"

        if self.bot_manager.update_bot(bot['bot_id'], config):
            return f"成功：机器人 {bot_handle} 配置已更新"
        return f"错误：更新机器人配置失败"

    def list_chats(self, bot_handle: str) -> List[str]:
        """List all chats for a bot."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        chats = self.bot_manager.list_chats(bot['bot_id'])
        if not chats:
            return []

        result = []
        for chat in chats:
            chat_id = chat['chat_id']
            chat_name = chat['chat_name']
            result.append(f'聊天名称：{chat_name} <{chat_id}>')
        return result

    def get_chat_history(self, bot_handle: str, chat_info: str) -> str:
        """Get chat history."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        chat_id = chat_info.split("<")[1].split(">")[0]
        history = self.bot_manager.get_chat_history(bot['bot_id'], chat_id)
        if not history:
            return "未找到消息记录"

        result = []
        for msg in history:
            sender = "机器人" if msg['is_from_bot'] else "用户"
            result.append(f"{sender}：{msg['message']}")
            result.append(f"时间：{msg['timestamp']}")
            result.append("-" * 30)
        return "\n".join(result)

    def clear_chat_history(self, bot_handle: str, chat_info: str) -> str:
        """Clear chat history."""
        bot = self.bot_manager.get_bot_by_handle(bot_handle)
        chat_id = chat_info.split("<")[1].split(">")[0]
        if self.bot_manager.clear_chat_history(bot['bot_id'], chat_id):
            return "成功：聊天记录已清除"
        return "提示：没有找到可清除的消息"

    def create_ui(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Telegram机器人管理系统") as interface:
            gr.Markdown("# Telegram机器人管理系统")

            with gr.Tab("创建机器人"):
                with gr.Row():
                    with gr.Column():
                        token_input = gr.Textbox(label="机器人Token")
                        bot_handle_input = gr.Textbox(label="机器人用户名（e.g. @johndoe_123_bot）")
                    with gr.Column(scale=3):
                        config_input = gr.Textbox(
                            label="配置（JSON格式）",
                            value=default_config_json,
                            lines=12, show_copy_button=True
                        )
                create_btn = gr.Button("创建机器人")
                create_output = gr.Textbox(label="操作结果")
                create_btn.click(
                    fn=self.create_bot,
                    inputs=[token_input, bot_handle_input, config_input],
                    outputs=create_output
                )

            with gr.Tab("管理机器人"):
                bot_select = gr.Dropdown(label="机器人列表", choices=[], interactive=True)
                with gr.Column():
                    with gr.Row():
                        bot_info = gr.Textbox(label="机器人状态")
                        bot_config = gr.Textbox(label="机器人配置（JSON格式）", show_copy_button=True,
                                                lines=6, scale=3, interactive=True)

                    with gr.Row():
                        start_btn = gr.Button("启动")
                        stop_btn = gr.Button("停止")
                        delete_btn = gr.Button("删除")
                        update_btn = gr.Button("更新机器人配置")

                    action_output = gr.Textbox(label="操作结果")

                bot_select.focus(lambda: gr.Dropdown(choices=self.list_bot_handles()), None, bot_select)
                (bot_select
                 .select(fn=self.get_bot_info, inputs=bot_select, outputs=bot_info)
                 .then(fn=self.get_bot_config, inputs=bot_select, outputs=bot_config))
                (start_btn
                 .click(fn=lambda x: asyncio.run_coroutine_threadsafe(
                    self.start_bot(x), self.loop).result(),
                        inputs=bot_select, outputs=action_output)
                 .then(fn=self.get_bot_info, inputs=bot_select, outputs=bot_info))
                (stop_btn
                 .click(
                    fn=lambda x: asyncio.run_coroutine_threadsafe(
                        self.stop_bot(x), self.loop).result(),
                    inputs=bot_select, outputs=action_output)
                 .then(fn=self.get_bot_info, inputs=bot_select, outputs=bot_info))
                (delete_btn
                 .click(
                    fn=lambda x: asyncio.run_coroutine_threadsafe(
                        self.delete_bot(x), self.loop).result(),
                    inputs=bot_select,
                    outputs=action_output)
                 .then(lambda: '', None, bot_info)
                 .then(lambda: '', None, bot_config)
                 .then(lambda: gr.Dropdown(choices=self.list_bot_handles()), None, bot_select))
                update_btn.click(
                    fn=self.update_bot_config,
                    inputs=[bot_select, bot_config],
                    outputs=action_output
                )

            with gr.Tab("聊天记录"):
                with gr.Row():
                    chat_bot_select = gr.Dropdown(label="机器人列表", choices=[], interactive=True)
                    chat_select = gr.Dropdown(label="聊天列表", choices=[], interactive=True)

                history_output = gr.Textbox(label="聊天历史", lines=10, show_copy_button=True)
                clear_history_btn = gr.Button("清除聊天记录", variant="secondary")
                chat_action_output = gr.Textbox(label="操作结果")

                chat_bot_select.focus(lambda: gr.Dropdown(choices=self.list_bot_handles()), None, chat_bot_select)
                chat_bot_select.select(fn=lambda x: gr.Dropdown(choices=self.list_chats(x)),
                                       inputs=chat_bot_select,
                                       outputs=chat_select)
                chat_select.select(fn=self.get_chat_history,
                                   inputs=[chat_bot_select, chat_select],
                                   outputs=history_output)
                (clear_history_btn
                 .click(
                    fn=self.clear_chat_history,
                    inputs=[chat_bot_select, chat_select],
                    outputs=chat_action_output)
                 .then(lambda: '', None, history_output)
                 .then(fn=lambda x: gr.Dropdown(choices=self.list_chats(x)),
                       inputs=chat_bot_select,
                       outputs=chat_select))

        return interface

    def run(self, server_name: str = None, server_port: int = 7860):
        """Run the Gradio interface.
        
        Args:
            server_name: Server name or IP to bind to (e.g., '0.0.0.0' for public access)
            server_port: Port number to run the server on
        """
        interface = self.create_ui()
        interface.queue()
        interface.launch(
            server_name=server_name,
            server_port=server_port,
            # share=server_name == "0.0.0.0"  # Enable sharing if binding to all interfaces
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行Telegram机器人管理系统")
    parser.add_argument("--host", default=None, help="服务器主机名或IP (例如: '0.0.0.0'表示公开访问)")
    parser.add_argument("--port", type=int, default=7860, help="服务器端口号")

    args = parser.parse_args()

    service = TelegramBotServiceGradio()
    service.run(server_name=args.host, server_port=args.port)
