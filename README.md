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

## 协作开发指南

### 分支管理

我们采用 Feature Branch Workflow 工作流程：

1. 主分支说明
   - `main`: 主分支，保持稳定可发布状态
   - `develop`: 开发分支，包含最新的开发特性

2. 功能开发流程
   ```bash
   # 1. 从 develop 分支(dev)创建功能分支
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name

   # 2. 在功能分支上进行开发
   git add .
   git commit -m "feat: 添加新功能"

   # 3. 定期同步 develop 分支(dev)的更新
   git checkout dev
   git pull origin dev
   git checkout feature/your-feature-name
   git rebase dev

   # 4. 完成功能后，创建 Pull Request
   git push origin feature/your-feature-name
   ```

3. 分支命名规范
   - 功能分支：`feature/功能名称`
   - 修复分支：`bugfix/问题描述`
   - 热修复分支：`hotfix/问题描述`

4. 提交信息规范
   ```
   feat: 添加新功能
   fix: 修复问题
   docs: 更新文档
   style: 代码格式调整
   refactor: 代码重构
   test: 添加测试
   chore: 构建过程或辅助工具的变动
   ```

### 代码审查

1. 所有代码变更都需要通过 Pull Request 进行
2. 至少需要一个审查者批准后才能合并
3. CI 检查必须通过
4. 解决所有冲突后才能合并

### 发布流程

1. 在 dev 分支完成功能开发和测试
2. 创建 release 分支进行发布准备
3. 完成测试后合并到 main 分支
4. 在 main 分支上添加版本标签

## 技术支持

如有问题，请提交 Issue 或联系技术支持。
