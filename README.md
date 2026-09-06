# QQ 机器人官方模块仓库

配套 [QQ 机器人框架](https://github.com/yskzctx/qqbot-framework)（v0.2.0+）的模块合集。

> 📖 **开发模块请先读 [模块开发指南](docs/模块开发指南.md)** —— 从 5 分钟入门到
> 装饰器 API、事件管道、配置界面、AI/系统/定时能力、实战案例、FAQ，一篇讲透。

## 安装模块

把想要的模块文件（`.py`，有 `.html` 的一并）复制到机器人的 `QQBotData\modules\` 文件夹，
几秒内自动加载，面板「模块」页即可查看和配置。

## 官方模块列表

| 模块 | 命令/触发 | 功能 | 配置界面 |
|---|---|---|---|
| **关键词自动回复** `auto_reply` | 按规则 | 关键词=回复 规则表；群/私聊开关；@限制；模糊匹配 | ✓ |
| **AI 对话** `ai_chat` | `ai 你好` | 带前缀调 AI 对话，支持人设、多轮记忆、群聊@触发 | ✓ |
| **入群欢迎** `group_welcome` | 自动 | 新人进群发欢迎语，模板支持 {nickname} {userid} | ✓ |
| **每日签到与积分** `sign_in` | `签到` `积分` `积分排行` | 随机积分、连签加成、排行榜 | ✓ |
| **防撤回提醒** `recall_alert` | 自动 | 群成员撤回消息时提醒 | ✓ |
| **定时消息** `scheduled_msg` | 自动 | `HH:MM\|group\|群号\|内容`，到点自动发，每日去重 | ✓ |
| **系统工具** `system_kit` | `系统 ...` | 管理员在 QQ 里执行命令/管理文件/查看系统状态（仅管理员） | ✓ |

每个模块都带**同名 `.html` 可视化配置界面**。数据存储在机器人
`QQBotData\data\`，升级/重装框架都不会丢失，也绝不回写模块文件。

## 自己写模块

```python
MODULE_INFO = {"name": "显示名", "description": "描述", "version": "0.1"}

async def on_event(bot, event):
    if event.get("raw_message") == "/签到":
        await bot.send_group_msg(event["group_id"], "签到成功！")
```

保存即生效（自动热重载）。完整能力一览：

- `@cmd` / `@event` / `@api` 装饰器（聊天命令、事件订阅+拦截、自有 HTTP API）
- 读写数据：`bot.app.get_module_config("<文件名>")`
- 调用 AI：`await bot.app.ai.chat([...])`
- 管理员判定：`bot.is_admin(uid)`
- 任意 OneBot 动作：`bot.call_action(...)`——点赞(`send_like`)、戳一戳、群打卡、
  群头衔、AI 语音、表情回应、群文件管理、OCR……130+ 动作全透传
- Python 标准库全开放：文件、命令、定时、网络……

👉 详见 **[模块开发指南](docs/模块开发指南.md)**

## 目录结构

```
├── README.md            本文件
├── docs/
│   └── 模块开发指南.md   ★ 完整开发文档
├── modules/             全部官方模块（.py + .html 配置界面）
└── tools/
    └── build_uis.py     配置界面生成器（开发工具）
```

## 声明与致谢

- 本框架与模块的 QQ 消息能力基于开源项目
  **[NapCat (NapCatQQ)](https://github.com/NapNeko/NapCatQQ)** 实现，
  版权归 NapNeko 团队所有，在此致谢。
- 模块仅用于自动化自己拥有或经授权使用的 QQ 小号，请遵守平台规则与当地法律法规，
  勿用于骚扰、垃圾信息、引流营销等任何违法违规用途。
- 使用注入类第三方工具存在账号被风控/封禁的风险，请自行评估并以小号操作，
  一切后果由使用者自行承担。
