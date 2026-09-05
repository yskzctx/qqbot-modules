# -*- coding: utf-8 -*-
"""模块集成测试：模拟 OneBot QQ 客户端，验证 6 个模块的实际行为。"""
import asyncio
import datetime
import json
import urllib.request

BASE = "http://127.0.0.1:2280"
WS_URL = "ws://127.0.0.1:2280/onebot/v11/ws?access_token=ob_token_123"
OB_TOKEN = "ob_token_123"
PANEL_PWD = "my_pwd_123"
results = []


def panel_post(path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        req.add_header("X-Access-Token", token)
    with urllib.request.urlopen(req, json.dumps(body).encode() if body is not None else None, timeout=8) as r:
        return json.loads(r.read())


def panel_get(path, token=None):
    req = urllib.request.Request(BASE + path)
    if token:
        req.add_header("X-Access-Token", token)
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())


async def main():
    import aiohttp
    async with aiohttp.ClientSession() as s:
        ws = await s.ws_connect(WS_URL)
        received = []

        async def reader():
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    continue
                pkt = json.loads(msg.data)
                if "echo" in pkt and "action" in pkt:
                    received.append(pkt)
                    data = {}
                    if pkt["action"] == "get_stranger_info":
                        data = {"nickname": "小明"}
                    await ws.send_str(json.dumps(
                        {"status": "ok", "retcode": 0, "data": data, "echo": pkt["echo"]}))

        reader_task = asyncio.create_task(reader())
        await asyncio.sleep(1)

        # 配置各模块
        if panel_get("/api/auth_state").get("need_setup"):
            panel_post("/api/setup", {"password": PANEL_PWD})
        t = panel_post("/api/login", {"password": PANEL_PWD})["token"]
        cfgs = {
            "auto_reply": {"enabled": True, "in_group": True, "in_private": True,
                           "fuzzy": False, "rules": "在吗=在的~\n菜单=菜单：/签到 /积分"},
            "group_welcome": {"enabled": True, "groups": "",
                              "template": "欢迎 {nickname}({userid}) 加入！"},
            "sign_in": {"enabled": True, "cmd_sign": "签到", "cmd_query": "积分",
                        "cmd_rank": "积分排行", "min_points": 1, "max_points": 10},
            "recall_alert": {"enabled": True, "template": "{user} 撤回了一条消息(群{group})"},
            "scheduled_msg": {"enabled": True, "jobs": ""},
        }
        for name, cfg in cfgs.items():
            panel_post(f"/api/modules/{name}/config", {"config": cfg}, token=t)

        async def send_event(ev):
            req = urllib.request.Request(
                BASE + f"/onebot/v11/events?access_token={OB_TOKEN}", method="POST")
            req.add_header("Content-Type", "application/json")
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: urllib.request.urlopen(
                    req, json.dumps(ev).encode(), timeout=8).read())

        async def wait_action(contains, timeout=15):
            for _ in range(timeout * 2):
                for pkt in received:
                    if contains in json.dumps(pkt, ensure_ascii=False):
                        return True
                await asyncio.sleep(0.5)
            return False

        def last_action():
            return json.dumps(received[-1], ensure_ascii=False) if received else "(无)"

        # 1. auto_reply：私聊"在吗" → 应回复"在的~"
        await send_event({"post_type": "message", "message_type": "private",
                          "raw_message": "在吗", "user_id": 10001})
        ok = await wait_action("在的~")
        results.append(("auto_reply 私聊触发", ok, last_action()))

        # 2. auto_reply：群聊不相干消息 → 不应触发
        n = len(received)
        await send_event({"post_type": "message", "message_type": "group",
                          "group_id": 888, "user_id": 10001, "raw_message": "今天天气不错"})
        await asyncio.sleep(2)
        results.append(("auto_reply 未命中不回复", len(received) == n, ""))

        # 3. sign_in：群聊"签到" → 应收到签到成功
        await send_event({"post_type": "message", "message_type": "group", "group_id": 888,
                          "user_id": 10001, "raw_message": "签到",
                          "sender": {"nickname": "小明"}})
        ok = await wait_action("签到成功")
        results.append(("sign_in 签到", ok, last_action()))

        # 4. sign_in：查询积分
        await send_event({"post_type": "message", "message_type": "group", "group_id": 888,
                          "user_id": 10001, "raw_message": "积分"})
        ok = await wait_action("当前积分")
        results.append(("sign_in 查积分", ok, last_action()))

        # 5. group_welcome：入群通知 → 应回复欢迎语（含昵称"小明"）
        await send_event({"post_type": "notice", "notice_type": "group_increase",
                          "group_id": 888, "user_id": 20002})
        ok = await wait_action("小明")
        results.append(("group_welcome 欢迎语", ok, last_action()))

        # 6. recall_alert：撤回通知
        await send_event({"post_type": "notice", "notice_type": "group_recall",
                          "group_id": 888, "user_id": 10001, "operator_id": 555})
        ok = await wait_action("撤回了一条消息")
        results.append(("recall_alert 撤回提醒", ok, last_action()))

        # 7. ai_chat：无 AI 配置 → 应回复"AI 调用失败"（证明链路通）
        await send_event({"post_type": "message", "message_type": "private",
                          "user_id": 10001, "raw_message": "ai 你好"})
        ok = await wait_action("AI 调用失败")
        results.append(("ai_chat 链路(未配AI报错)", ok, last_action()))

        # 8. scheduled_msg：排一个 90 秒后的任务
        target = (datetime.datetime.now() + datetime.timedelta(seconds=90)).strftime("%H:%M")
        panel_post("/api/modules/scheduled_msg/config",
                   {"config": {"enabled": True, "jobs": f"{target}|group|888|定时消息测试"}},
                   token=t)
        ok = await wait_action("定时消息测试", timeout=150)
        results.append(("scheduled_msg 定时触发", ok, last_action()))

        print("\n===== 测试结果 =====")
        passed = 0
        for name, ok, detail in results:
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  | " + detail))
            passed += ok
        print(f"{passed}/{len(results)} 通过")

        await ws.close()
        reader_task.cancel()


asyncio.run(main())
