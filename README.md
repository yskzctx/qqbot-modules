# QQ 机器人官方模块仓库

配套 [qqbot-framework](https://github.com/yskzctx/qqbot-framework) 的模块合集。
把想要的模块文件（`.py`，界面 `.html` 一并）复制到机器人的
`QQBotData\modules\` 文件夹，几秒内自动加载，在面板「模块」页即可看到并配置。

## 模块列表

| 模块 | 文件 | 功能 | 默认命令/触发 |
|---|---|---|---|
| 关键词自动回复 | `auto_reply` | 关键词=回复 规则表，支持群/私聊开关、@限制、模糊匹配 | 按规则 |
| AI 对话 | `ai_chat` | 消息带前缀调 AI（用面板「AI 配置」），支持人设与多轮历史 | `ai 你好` |
| 入群欢迎 | `group_welcome` | 新人进群发欢迎语，模板支持 {nickname} {userid} | 自动 |
| 每日签到与积分 | `sign_in` | 签到得随机积分、连签加成、查询与排行榜 | `签到` `积分` `积分排行` |
| 防撤回提醒 | `recall_alert` | 群里撤回消息时提醒 | 自动 |
| 定时消息 | `scheduled_msg` | 到点自动发消息，任务格式 `HH:MM\|group\|群号\|内容` | 自动 |

每个模块都带同名 `.html` 配置界面：面板 → 模块 → 点对应模块即可可视化配置，
数据存在机器人 `QQBotData\data\` 里，改配置不用重启。

## 安装

```
1. 下载本仓库 modules\ 文件夹里你想要的 .py + .html
2. 复制到机器人目录的 QQBotData\modules\
3. 约 3 秒自动热重载（或在面板点「重载模块」）
4. 面板 → 模块 → 选中模块 → 按需配置
```

## 自己写模块（规则速查）

- 一个 `.py` = 一个模块，可带同名 `.html` 作为配置界面
- 模块内定义（全部可选）：
  - `MODULE_INFO = {"name": "显示名", "description": "描述", "version": "0.1"}`
  - `register(app)` —— 加载时调用
  - `async def on_event(bot, event)` —— 收到 QQ 事件（消息/通知/请求）
  - `def on_config(app, config)` —— 面板保存该模块配置时回调
- 读写自己的数据：`bot.app.get_module_config("<文件名>")` / `bot.app.set_module_config(...)`（存 `QQBotData\data\<文件名>.json`，不回写模块文件）
- 调 AI：`await bot.app.ai.chat([...])`（OpenAI 兼容，面板「AI 配置」填写）
- 发消息：`await bot.send_group_msg(group_id, text)` / `bot.send_private_msg(user_id, text)` / `bot.call_action(...)`
- 下划线开头的 `.py` 不会被当作模块加载
- 修改 modules 文件夹后自动热重载，无需重启机器人

## 免责声明

模块仅用于自动化自己的 QQ 账号，请遵守平台规则与当地法规，勿用于骚扰、垃圾信息等用途。
