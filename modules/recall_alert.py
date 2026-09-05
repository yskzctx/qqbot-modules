"""防撤回提醒模块：群里有人撤回消息时发提醒。

- 提醒文案支持 {user}（撤回者）{operator}（执行撤回者，通常管理员）{group}（群号）
"""

MODULE_INFO = {"name": "防撤回提醒", "description": "群成员撤回消息时发出提醒", "version": "1.0"}


async def on_event(bot, event):
    if event.get("post_type") != "notice" or event.get("notice_type") != "group_recall":
        return
    cfg = bot.app.get_module_config("recall_alert")
    if not cfg.get("enabled", True):
        return

    text = (str(cfg.get("template", "{user} 撤回了一条消息（群 {group}）"))
            .replace("{user}", str(event.get("user_id", "?")))
            .replace("{operator}", str(event.get("operator_id", "?")))
            .replace("{group}", str(event.get("group_id", "?"))))
    await bot.send_group_msg(event.get("group_id"), text)
