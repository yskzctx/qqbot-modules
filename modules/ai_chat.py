"""AI 对话模块：消息带触发前缀时调用核心 AI 配置（OpenAI 兼容）对话。

- 每个用户独立保留最近 N 轮历史（存 QQBotData/data/ai_chat.json）
- 支持私聊 / 群聊开关；群聊中可配置为仅 @机器人 触发
- 需要「AI 配置」页填好 API 地址、密钥、模型 ID
"""

MODULE_INFO = {"name": "AI 对话", "description": "带前缀的消息走 AI 对话，支持人设与多轮历史", "version": "1.0"}

_histories: dict[str, list] = {}   # user_key -> [{"role","content"},...]
MAX_KEEP = 10                      # 本地最多保留轮数（超出裁剪）


def _at_me(event) -> bool:
    msg = event.get("message")
    if isinstance(msg, list):
        return any(isinstance(seg, dict) and seg.get("type") == "at" for seg in msg)
    return "[CQ:at" in str(msg or "")


async def on_event(bot, event):
    if event.get("post_type") != "message":
        return
    cfg = bot.app.get_module_config("ai_chat")
    if not cfg.get("enabled", True):
        return

    is_group = event.get("message_type") == "group"
    if is_group:
        if not cfg.get("in_group", False):
            return
        if not _at_me(event):
            return
    elif not cfg.get("in_private", True):
        return

    prefix = str(cfg.get("prefix", "ai "))
    raw = str(event.get("raw_message", "")).strip()
    if is_group and _at_me(event):
        # 群聊 @ 触发时去掉开头的 CQ at 段文本
        raw = raw.lstrip("@").strip()
    if not raw.startswith(prefix):
        return
    question = raw[len(prefix):].strip()
    if not question:
        return

    user_key = f"{event.get('user_id')}"
    max_history = int(cfg.get("max_history", 6) or 0)
    history = _histories.setdefault(user_key, [])[-max_history * 2:]

    messages = []
    system_prompt = str(cfg.get("system_prompt", "") or "").strip()
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages += history
    messages.append({"role": "user", "content": question})

    try:
        reply = await bot.app.ai.chat(messages)
    except Exception as e:
        reply = f"AI 调用失败：{e}"

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": reply})
    _histories[user_key] = history[-MAX_KEEP * 2:]

    if is_group:
        await bot.send_group_msg(event["group_id"], reply)
    else:
        await bot.send_private_msg(event["user_id"], reply)
