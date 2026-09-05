"""定时消息模块：按配置在指定时刻自动向群/私聊发送消息。

任务格式（每行一条，面板可视化编辑）：
    HH:MM|group|目标群号|消息内容
    HH:MM|private|目标QQ号|消息内容

实现说明：模块内部用一个守护线程每 20 秒对表一次，命中时刻后通过
asyncio.run_coroutine_threadsafe 把发送动作投回核心事件循环，天然去重
（同一任务每天只发一次）。
"""
import asyncio
import datetime
import threading
import time

MODULE_INFO = {"name": "定时消息", "description": "到点自动向群/私聊发送定时消息", "version": "1.0"}

_state = {"loop": None, "thread": None, "sent": {}}


def _capture_loop(bot):
    try:
        _state["loop"] = asyncio.get_running_loop()
    except RuntimeError:
        pass
    _ensure_thread(bot)


def _ensure_thread(bot):
    if _state["thread"] and _state["thread"].is_alive():
        return
    _state["thread"] = threading.Thread(target=_worker, args=(bot,), daemon=True)
    _state["thread"].start()


def register(app):
    _capture_loop(app.bot)


def _worker(bot):
    while True:
        time.sleep(20)
        try:
            _tick(bot)
        except Exception:
            pass


def _tick(bot):
    if _state["loop"] is None:
        return
    cfg = bot.app.get_module_config("scheduled_msg")
    if not cfg.get("enabled", True):
        return

    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    hm = now.strftime("%H:%M")
    _state["sent"] = {k: v for k, v in _state["sent"].items() if v == today}

    for line in str(cfg.get("jobs", "")).splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        hhmm, kind, target = parts[0], parts[1].lower(), parts[2]
        text = "|".join(parts[3:])
        if not (len(hhmm) == 5 and hhmm[2] == ":" and hhmm[:2].isdigit() and hhmm[3:].isdigit()):
            continue
        key = f"{hhmm}|{kind}|{target}|{text[:30]}"
        if hhmm != hm or _state["sent"].get(key) == today:
            continue
        _state["sent"][key] = today
        try:
            if kind == "group":
                coro = bot.send_group_msg(int(target), text)
            elif kind == "private":
                coro = bot.send_private_msg(int(target), text)
            else:
                continue
            asyncio.run_coroutine_threadsafe(coro, _state["loop"])
        except (ValueError, RuntimeError):
            continue


async def on_event(bot, event):
    _capture_loop(bot)
