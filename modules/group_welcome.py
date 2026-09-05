"""入群欢迎模块：新成员进群时发送欢迎语。

- 模板支持 {nickname} 与 {userid} 占位符
- groups 留空 = 对所有群生效；填群号（逗号分隔）= 仅这些群生效
"""

MODULE_INFO = {"name": "入群欢迎", "description": "新成员进群时自动发送可定制的欢迎语", "version": "1.0"}


def _render(template: str, nickname: str, user_id) -> str:
    return (str(template or "")
            .replace("{nickname}", nickname)
            .replace("{userid}", str(user_id)))


async def on_event(bot, event):
    if event.get("post_type") != "notice" or event.get("notice_type") != "group_increase":
        return
    cfg = bot.app.get_module_config("group_welcome")
    if not cfg.get("enabled", True):
        return

    group_id = event.get("group_id")
    allow = str(cfg.get("groups", "") or "").replace("，", ",").strip()
    if allow:
        allow_list = [g.strip() for g in allow.split(",") if g.strip()]
        if str(group_id) not in allow_list:
            return

    user_id = event.get("user_id")
    nickname = str(user_id)
    try:
        info = await bot.get_stranger_info(user_id)
        nickname = (info.get("data") or {}).get("nickname") or nickname
    except Exception:
        pass

    text = _render(cfg.get("template", "欢迎 {nickname} 加入本群！"), nickname, user_id)
    await bot.send_group_msg(group_id, text)
