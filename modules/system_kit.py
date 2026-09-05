"""系统工具模块：让管理员直接在 QQ 里执行系统级操作。

可用命令（默认前缀"系统"，可在配置里改）：
    系统                          查看帮助
    系统状态                      CPU / 内存 / 磁盘概览
    系统进程 [关键词]             资源占用前 8 的进程
    系统执行 <命令>               执行 PowerShell 命令（如 创建文件夹/删文件/装软件）
    系统目录 <路径>               列出目录内容
    系统读取 <路径>               读取文本文件
    系统写入 <路径>|<内容>        写入文本文件
    系统建夹 <路径>               创建文件夹（含多级）
    系统删除 <路径>               删除文件或整个文件夹

安全机制：
- 仅管理员可用（config.json -> permissions.admins）
- 删除操作可在面板里单独关闭
- 所有执行内容写入日志（logs/framework.log）
"""
import asyncio
import datetime
import os
import shutil
import subprocess

MODULE_INFO = {"name": "系统工具", "description": "管理员专属：在QQ里执行命令、管理文件、查看系统状态", "version": "1.0"}

MAX_OUT = 1500


def _prefix(cfg) -> str:
    return str(cfg.get("cmd_prefix", "系统") or "系统")


async def _reply(bot, event, text):
    text = str(text).strip()
    if not text:
        text = "(无输出)"
    if event.get("message_type") == "group":
        await bot.send_group_msg(event["group_id"], text[:MAX_OUT])
    else:
        await bot.send_private_msg(event["user_id"], text[:MAX_OUT])


def _run_ps(command: str, timeout: int = 60) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                       capture_output=True, timeout=timeout)
    out = (r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")).strip()
    return out or "(无输出)"


def _status_text() -> str:
    import psutil
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    lines = [f"CPU: {cpu}%  内存: {mem.percent}% ({mem.used // 1048576}/{mem.total // 1048576}MB)"]
    for d in psutil.disk_partitions():
        if d.fstype:
            try:
                u = psutil.disk_usage(d.mountpoint)
                lines.append(f"磁盘 {d.device} {u.percent}% ({u.free // 1073741824}GB 可用)")
            except (PermissionError, OSError):
                pass
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    lines.append(f"开机时间: {boot:%Y-%m-%d %H:%M}")
    return "\n".join(lines)


def _procs_text(keyword: str = "") -> str:
    import psutil
    rows = []
    for p in psutil.process_iter(["name", "memory_info", "cpu_percent"]):
        try:
            name = p.info["name"] or ""
            if keyword and keyword.lower() not in name.lower():
                continue
            rows.append((name, p.info["memory_info"].rss if p.info["memory_info"] else 0))
        except Exception:
            continue
    rows.sort(key=lambda x: -x[1])
    return "\n".join(f"{n}  {m // 1048576}MB" for n, m in rows[:8]) or "(未找到)"


HELP = """系统工具命令：
系统状态 —— CPU/内存/磁盘
系统进程 [关键词]
系统执行 <PowerShell命令>
系统目录 <路径>
系统读取 <路径>
系统写入 <路径>|<内容>
系统建夹 <路径>
系统删除 <路径>"""


async def on_event(bot, event):
    if event.get("post_type") != "message":
        return
    cfg = bot.app.get_module_config("system_kit")
    prefix = _prefix(cfg)
    raw = str(event.get("raw_message", "")).strip()
    if not raw.startswith(prefix):
        return

    uid = event.get("user_id")
    if not bot.app.is_admin(uid):
        await _reply(bot, event, "该命令仅管理员可用（permissions.admins 中配置）")
        return

    body = raw[len(prefix):].strip()
    loop = asyncio.get_running_loop()
    log = bot.app.log if hasattr(bot.app, "log") else None
    try:
        if body == "" or body == "帮助":
            await _reply(bot, event, HELP)

        elif body.startswith("状态"):
            await _reply(bot, event, await loop.run_in_executor(None, _status_text))

        elif body.startswith("进程"):
            kw = body[2:].strip()
            await _reply(bot, event, await loop.run_in_executor(None, _procs_text, kw))

        elif body.startswith("执行 "):
            cmd = body[3:].strip()
            await _reply(bot, event, await loop.run_in_executor(None, _run_ps, cmd))

        elif body.startswith("目录 "):
            path = body[3:].strip()
            entries = sorted(os.listdir(path))
            out = []
            for e in entries[:60]:
                full = os.path.join(path, e)
                out.append(("[目录] " if os.path.isdir(full) else "[文件] ") + e)
            await _reply(bot, event, "\n".join(out) or "(空目录)")

        elif body.startswith("读取 "):
            path = body[3:].strip()
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                await _reply(bot, event, f.read(MAX_OUT))

        elif body.startswith("写入 "):
            rest = body[3:].strip()
            if "|" not in rest:
                await _reply(bot, event, "格式：系统写入 <路径>|<内容>")
                return
            path, content = rest.split("|", 1)
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            await _reply(bot, event, f"已写入 {path}（{len(content)} 字符）")

        elif body.startswith("建夹 "):
            path = body[3:].strip()
            os.makedirs(path, exist_ok=True)
            await _reply(bot, event, f"已创建文件夹 {path}")

        elif body.startswith("删除 "):
            if not cfg.get("allow_delete", True):
                await _reply(bot, event, "删除操作已在面板中关闭")
                return
            path = body[3:].strip()
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)
            else:
                await _reply(bot, event, "路径不存在")
                return
            await _reply(bot, event, f"已删除 {path}")

        else:
            await _reply(bot, event, "未知子命令，发送「系统」查看帮助")
    except Exception as e:
        await _reply(bot, event, f"执行失败：{e}")
