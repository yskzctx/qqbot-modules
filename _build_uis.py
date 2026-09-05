# -*- coding: utf-8 -*-
"""临时脚本：为模块生成统一风格的配置界面 HTML（不在仓库内）。"""
import os

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: "Microsoft YaHei", sans-serif; color: #e6edf3;
         background: transparent; padding: 6px 2px; margin: 0; }}
  h3 {{ margin: 4px 0 2px; font-size: 15px; }}
  .hint {{ font-size: 12px; color: #8b98a5; margin: 0 0 4px; }}
  label {{ display: block; font-size: 13px; color: #8b98a5; margin: 12px 0 6px; }}
  input[type=text], input[type=number], textarea {{ width: 100%; max-width: 480px;
    background: #212a33; color: #e6edf3; border: 1px solid #2c3742; border-radius: 8px;
    padding: 9px 12px; font-size: 13px; outline: none; box-sizing: border-box; }}
  textarea {{ min-height: 90px; font-family: Consolas, monospace; }}
  input:focus, textarea:focus {{ border-color: #4c8dff; }}
  .check {{ display: flex; align-items: center; gap: 8px; margin: 10px 0;
    font-size: 13px; color: #e6edf3; }}
  .check input {{ width: auto; }}
  button {{ background: #4c8dff; color: #fff; border: 0; border-radius: 8px;
    padding: 9px 20px; font-size: 13px; cursor: pointer; margin-top: 14px; }}
  #tip {{ margin-top: 10px; font-size: 12px; color: #2ea86b; min-height: 16px; }}
</style>
</head>
<body>
  <h3>{title} — 配置</h3>
  <p class="hint">数据保存在 QQBotData/data/，不会修改模块文件；保存后立即生效</p>
{body}
  <button onclick="save()">保存</button>
  <div id="tip"></div>
<script>
const token = new URLSearchParams(location.search).get("token") || "";
const base = "/api/modules/{module}/config";
const H = {{"Content-Type": "application/json", "X-Access-Token": token}};

const FIELDS = {fields};

async function load(){{
  try {{
    const cfg = await (await fetch(base, {{headers: H}})).json();
    for (const [key, type] of Object.entries(FIELDS)) {{
      const el = document.getElementById(key);
      if (!el) continue;
      if (type === "check") el.checked = !!cfg[key];
      else el.value = cfg[key] !== undefined && cfg[key] !== null ? cfg[key] : "";
    }}
  }} catch(e) {{ tip("加载失败: " + e.message, true); }}
}}

async function save(){{
  const cfg = {{}};
  for (const [key, type] of Object.entries(FIELDS)) {{
    const el = document.getElementById(key);
    if (!el) continue;
    if (type === "check") cfg[key] = el.checked;
    else if (type === "number") cfg[key] = Number(el.value || 0);
    else cfg[key] = el.value;
  }}
  try {{
    const r = await fetch(base, {{method: "POST", headers: H,
      body: JSON.stringify({{config: cfg}})}});
    const d = await r.json();
    tip(d.ok ? "已保存 ✓" : "保存失败: " + d.error, !d.ok);
  }} catch(e) {{ tip("保存失败: " + e.message, true); }}
}}
function tip(msg, err){{ const t = document.getElementById("tip");
  t.textContent = msg; t.style.color = err ? "#e5534b" : "#2ea86b"; }}
load();
</script>
</body>
</html>
"""

CHECK = '  <div class="check"><input type="checkbox" id="{k}" {checked}><span>{label}</span></div>'
INPUT = '  <label>{label}</label>\n  <input type="{itype}" id="{k}" placeholder="{ph}">'
AREA = '  <label>{label}</label>\n  <textarea id="{k}" placeholder="{ph}"></textarea>'


def build(module, title, fields, defaults):
    parts, fmap = [], {}
    for f in fields:
        kind, key, label = f[0], f[1], f[2]
        ph = f[3] if len(f) > 3 else ""
        fmap[key] = kind
        if kind == "check":
            parts.append(CHECK.format(k=key, label=label,
                                      checked="checked" if defaults.get(key) else ""))
        elif kind == "textarea":
            parts.append(AREA.format(k=key, label=label, ph=ph))
        else:
            parts.append(INPUT.format(k=key, label=label, ph=ph,
                                      itype="number" if kind == "number" else "text"))
    html = TPL.format(title=title, body="\n".join(parts), module=module,
                      fields=__import__("json").dumps(fmap, ensure_ascii=False))
    path = os.path.join(os.path.dirname(__file__), "modules", module + ".html")
    open(path, "w", encoding="utf-8").write(html)
    print("built", module + ".html")


build("auto_reply", "关键词自动回复", [
    ("check", "enabled", "启用模块"),
    ("check", "in_group", "群聊生效"),
    ("check", "in_private", "私聊生效"),
    ("check", "group_at_only", "群聊必须 @机器人 才触发"),
    ("check", "fuzzy", "包含匹配（勾选=消息包含关键词即回复；否则需完全相等）"),
    ("textarea", "rules", "回复规则（每行一条：关键词=回复）",
     "在吗=在的~\n你好=你好呀！\n菜单=菜单：/签到 /积分 /排行"),
], {"enabled": True, "in_group": True, "in_private": True})

build("ai_chat", "AI 对话", [
    ("check", "enabled", "启用模块"),
    ("check", "in_group", "群聊生效"),
    ("check", "in_private", "私聊生效"),
    ("text", "prefix", "触发前缀（消息以它开头才调 AI，避免所有消息都消耗额度）", "ai "),
    ("textarea", "system_prompt", "人设 / System Prompt", "你是一个友好的中文助手，回答简洁。"),
    ("number", "max_history", "携带历史轮数（每轮=一问一答）", "6"),
], {"enabled": True, "in_private": True, "prefix": "ai ", "max_history": 6,
    "system_prompt": "你是一个友好的中文助手，回答简洁。"})

build("group_welcome", "入群欢迎", [
    ("check", "enabled", "启用模块"),
    ("text", "groups", "生效群号（逗号分隔，留空=所有群）", "123456,654321"),
    ("textarea", "template", "欢迎语模板（支持 {{nickname}} {{userid}}）",
     "欢迎 {{nickname}}（{{userid}}）加入本群！先看群公告哦~"),
], {"enabled": True,
    "template": "欢迎 {{nickname}}（{{userid}}）加入本群！先看群公告哦~"})

build("sign_in", "每日签到与积分", [
    ("check", "enabled", "启用模块"),
    ("text", "cmd_sign", "签到触发词", "签到"),
    ("text", "cmd_query", "查积分触发词", "积分"),
    ("text", "cmd_rank", "排行榜触发词", "积分排行"),
    ("number", "min_points", "每次签到最少积分", "1"),
    ("number", "max_points", "每次签到最多积分", "10"),
], {"enabled": True, "cmd_sign": "签到", "cmd_query": "积分",
    "cmd_rank": "积分排行", "min_points": 1, "max_points": 10})

build("recall_alert", "防撤回提醒", [
    ("check", "enabled", "启用模块"),
    ("textarea", "template", "提醒文案（支持 {{user}} {{operator}} {{group}}）",
     "{{user}} 撤回了一条消息（群 {{group}}），手速再快也没用~"),
], {"enabled": True,
    "template": "{{user}} 撤回了一条消息（群 {{group}}），手速再快也没用~"})

build("scheduled_msg", "定时消息", [
    ("check", "enabled", "启用模块"),
    ("textarea", "jobs", "定时任务（每行一条：HH:MM|group或private|目标号码|内容）",
     "08:00|group|123456|大家早上好！\n22:30|private|10001|该休息啦"),
], {"enabled": True})

print("all UIs built")
