"""每日签到与积分模块。

- 签到：每人每天一次，随机积分（范围可配），连续签到有加成提示
- 查积分 / 积分排行（前 5 名）命令可自定义
- 用户数据与昵称缓存存在 QQBotData/data/sign_in.json
"""

import datetime
import random

MODULE_INFO = {"name": "每日签到与积分", "description": "签到得积分，支持查询与排行榜", "version": "1.0"}


def _today() -> str:
    return datetime.date.today().isoformat()


def _yesterday() -> str:
    return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


async def _reply(bot, event, text):
    if event.get("message_type") == "group":
        await bot.send_group_msg(event["group_id"], text)
    else:
        await bot.send_private_msg(event["user_id"], text)


async def on_event(bot, event):
    if event.get("post_type") != "message":
        return
    cfg = bot.app.get_module_config("sign_in")
    if not cfg.get("enabled", True):
        return

    raw = str(event.get("raw_message", "")).strip()
    cmd_sign = str(cfg.get("cmd_sign", "签到"))
    cmd_query = str(cfg.get("cmd_query", "积分"))
    cmd_rank = str(cfg.get("cmd_rank", "积分排行"))
    if raw not in (cmd_sign, cmd_query, cmd_rank):
        return

    data = bot.app.get_module_config("sign_in")
    users = data.setdefault("users", {})
    uid = str(event.get("user_id"))
    me = users.setdefault(uid, {"points": 0, "days": 0, "last": "", "name": ""})
    me["name"] = (event.get("sender") or {}).get("nickname") or me.get("name") or uid

    if raw == cmd_sign:
        if me.get("last") == _today():
            await _reply(bot, event, f"今天已经签到过啦，当前积分 {me['points']} 分")
            return
        lo = int(cfg.get("min_points", 1) or 1)
        hi = max(int(cfg.get("max_points", 10) or 10), lo)
        gain = random.randint(lo, hi)
        streak_bonus = 5 if me.get("last") == _yesterday() else 0
        me["points"] += gain + streak_bonus
        me["days"] += 1
        me["last"] = _today()
        bonus_txt = f"（含连续签到加成 +{streak_bonus}）" if streak_bonus else ""
        await _reply(bot, event,
                     f"签到成功！获得 {gain} 分{bonus_txt}，当前 {me['points']} 分，"
                     f"已连续/累计签到 {me['days']} 天")
        bot.app.set_module_config("sign_in", data)

    elif raw == cmd_query:
        await _reply(bot, event, f"当前积分：{me['points']} 分，已签到 {me['days']} 天")

    elif raw == cmd_rank:
        if not users:
            await _reply(bot, event, "还没有人签到过哦")
            return
        top = sorted(users.values(), key=lambda u: -u.get("points", 0))[:5]
        lines = [f"{i + 1}. {u.get('name', '?')} —— {u.get('points', 0)} 分"
                 for i, u in enumerate(top)]
        await _reply(bot, event, "积分排行榜：\n" + "\n".join(lines))
