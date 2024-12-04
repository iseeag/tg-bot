# Telegram 机器人管理系统

这是一个基于 Gradio 的 Telegram 机器人管理系统，支持创建、管理和监控多个 Telegram 机器人。系统提供了友好的中文界面，可以方便地管理机器人配置和查看聊天记录。

## 功能特点

- 创建和管理多个 Telegram 机器人
- 实时启动/停止机器人服务
- 更新机器人配置
- 查看和清除聊天记录
- 完全中文化的用户界面
- 支持 OpenAI 接口进行智能对话

## 环境要求

- Python 3.8 或更高版本
- SQLite3 数据库（已内置在 Python 中）

## 安装步骤

1. 克隆项目代码：
```bash
git clone https://github.com/iseeag/tg-bot.git
cd tg-bot
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并添加以下配置：
```
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，如果使用其他API端点
```

## 启动服务

1. 启动 Gradio 界面：
```bash
python service_gradio.py
```

2. 可选启动参数：
```bash
# 指定主机和端口
python service_gradio.py  # --host 0.0.0.0 --port 7860
```

## 使用说明

### 创建机器人

1. 打开"创建机器人"标签页
2. 输入从 @BotFather 获取的机器人 Token
3. 输入机器人用户名（例如：@your_bot_name）
4. 配置机器人参数（JSON 格式）
5. 点击"创建机器人"按钮

### 管理机器人

1. 在"管理机器人"标签页中选择要管理的机器人
2. 可以进行以下操作：
   - 启动/停止机器人
   - 更新机器人配置
   - 删除机器人

### 查看聊天记录

1. 打开"聊天记录"标签页
2. 选择要查看的机器人
3. 选择具体的聊天会话
4. 查看或清除聊天记录

## 常见问题

1. 如果遇到数据库错误，请确保程序有写入权限
2. 确保所有的 Token 都是有效的
3. 如果机器人无法启动，请检查网络连接和 Token 是否正确

## 注意事项

- 请妥善保管机器人 Token，不要泄露给他人
- 建议定期备份数据库文件
- 在公网部署时，建议配置适当的安全措施

## 技术支持

如有问题，请提交 Issue 或联系技术支持。
