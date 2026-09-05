"""关键词自动回复模块。

配置项（面板可视化编辑）：
- enabled: 总开关
- in_group / in_private: 群聊/私聊开关
- group_at_only: 群聊是否必须 @机器人 才触发
- fuzzy: 关键词包含匹配（否则完全相等匹配）
- rules: 每行一条 "关键词=回复"
"""


def _at_me(event) -> bool:
    msg = event.get("message")
    if isinstance(msg, list):
        return any(isinstance(seg, dict) and seg.get("type") == "at" for seg in msg)
    return "[CQ:at" in str(msg or "")


def _parse_rules(text: str) -> list[tuple[str, str]]:
    rules = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if "=" in line:
            kw, reply = line.split("=", 1)
            kw, reply = kw.strip(), reply.strip()
            if kw:
                rules.append((kw, reply))
    return rules


async def on_event(bot, event):
    if event.get("post_type") != "message":
        return
    cfg = bot.app.get_module_config("auto_reply")

    if not cfg.get("enabled", True):
        return
    is_group = event.get("message_type") == "group"
    if is_group:
        if not cfg.get("in_group", True):
            return
        if cfg.get("group_at_only") and not _at_me(event):
            return
    elif not cfg.get("in_private", True):
        return

    raw = str(event.get("raw_message", "")).strip()
    fuzzy = cfg.get("fuzzy", False)
    for kw, reply in _parse_rules(cfg.get("rules", "")):
        if (kw in raw) if fuzzy else (raw == kw):
            if is_group:
                await bot.send_group_msg(event["group_id"], reply)
            else:
                await bot.send_private_msg(event["user_id"], reply)
            return
