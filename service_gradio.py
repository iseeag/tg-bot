import asyncio
import json
import threading
from typing import Dict, List

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

    async def start_bot(self, bot_id: str) -> str:
        """Start a bot."""
        if await self.bot_manager.start_bot(bot_id):
            return f"成功：机器人 {bot_id} 已启动"
        return f"错误：启动机器人 {bot_id} 失败"

    async def stop_bot(self, bot_id: str) -> str:
        """Stop a bot."""
        if await self.bot_manager.stop_bot(bot_id):
            return f"成功：机器人 {bot_id} 已停止"
        return f"错误：停止机器人 {bot_id} 失败"

    async def delete_bot(self, bot_id: str) -> str:
        """Delete a bot."""
        if await self.bot_manager.delete_bot(bot_id):
            return f"成功：机器人 {bot_id} 已删除"
        return f"错误：删除机器人 {bot_id} 失败"

    def update_bot(self, bot_id: str, config_str: str) -> str:
        """Update bot configuration."""
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return "错误：JSON配置格式无效"

        if self.bot_manager.update_bot(bot_id, config):
            return f"成功：机器人 {bot_id} 配置已更新"
        return f"错误：更新机器人配置失败"

    def list_chats(self, bot_id: str) -> str:
        """List all chats for a bot."""
        chats = self.bot_manager.list_chats(bot_id)
        if not chats:
            return "未找到聊天记录"

        result = []
        for chat in chats:
            result.append(f"聊天ID：{chat['chat_id']}")
            result.append(f"聊天名称：{chat['chat_name']}")
            result.append("-" * 30)
        return "\n".join(result)

    def get_chat_history(self, bot_id: str, chat_id: str) -> str:
        """Get chat history."""
        history = self.bot_manager.get_chat_history(bot_id, chat_id)
        if not history:
            return "未找到消息记录"

        result = []
        for msg in history:
            sender = "机器人" if msg['is_from_bot'] else "用户"
            result.append(f"{sender}：{msg['message']}")
            result.append(f"时间：{msg['timestamp']}")
            result.append("-" * 30)
        return "\n".join(result)

    def create_ui(self):
        """Create the Gradio interface."""
        with gr.Blocks(title="Telegram机器人管理系统") as interface:
            gr.Markdown("# Telegram机器人管理系统")

            with gr.Tab("创建机器人"):
                with gr.Row():
                    with gr.Column():
                        token_input = gr.Textbox(label="机器人Token")
                        bot_handle_input = gr.Textbox(label="机器人用户名")
                    with gr.Column(scale=2):
                        config_input = gr.Textbox(
                            label="配置（JSON格式）",
                            value=default_config_json,
                            lines=4
                        )
                create_btn = gr.Button("创建机器人")
                create_output = gr.Textbox(label="结果")
                create_btn.click(
                    fn=self.create_bot,
                    inputs=[token_input, bot_handle_input, config_input],
                    outputs=create_output
                )

            with gr.Tab("管理机器人"):
                refresh_btn = gr.Button("刷新机器人列表")
                bot_list = gr.Textbox(label="机器人列表", lines=10)
                refresh_btn.click(
                    fn=self.format_bot_list,
                    inputs=[],
                    outputs=bot_list
                )

                with gr.Row():
                    bot_id_input = gr.Textbox(label="机器人ID")
                    action_btns = gr.Group()
                    with action_btns:
                        start_btn = gr.Button("启动")
                        stop_btn = gr.Button("停止")
                        delete_btn = gr.Button("删除")

                with gr.Row():
                    config_update = gr.Textbox(
                        label="新配置（JSON格式）",
                        lines=5
                    )
                    update_btn = gr.Button("更新")

                action_output = gr.Textbox(label="操作结果")

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

            with gr.Tab("聊天记录"):
                with gr.Row():
                    chat_bot_id = gr.Textbox(label="机器人ID")
                    chat_id = gr.Textbox(label="聊天ID")

                list_chats_btn = gr.Button("列出聊天记录")
                chats_output = gr.Textbox(label="聊天列表", lines=5)

                view_history_btn = gr.Button("查看聊天历史")
                history_output = gr.Textbox(label="聊天历史", lines=10)

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
