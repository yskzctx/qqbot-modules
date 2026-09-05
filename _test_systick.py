# -*- coding: utf-8 -*-
"""system_kit 模块测试：权限门槛 + 文件操作 + 命令执行。"""
import asyncio
import json
import os
import urllib.request

BASE = "http://127.0.0.1:2280"
WS_URL = "ws://127.0.0.1:2280/onebot/v11/ws?access_token=ob_token_123"
OB_TOKEN = "ob_token_123"
PANEL_PWD = "my_pwd_123"
ADMIN = 10001
NON_ADMIN = 99999
TMP = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "qqbot_systest")
results = []


def panel(path, body=None, token=None, method="POST"):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        req.add_header("X-Access-Token", token)
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(req, data, timeout=8) as r:
        return json.loads(r.read())


async def main():
    import aiohttp
    async with aiohttp.ClientSession() as s:
        ws = await s.ws_connect(WS_URL)
        received = []

        async def reader():
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    pkt = json.loads(msg.data)
                    if "echo" in pkt and "action" in pkt:
                        received.append(pkt)
                        await ws.send_str(json.dumps(
                            {"status": "ok", "retcode": 0, "data": {}, "echo": pkt["echo"]}))

        asyncio.get_event_loop().create_task(reader())
        await asyncio.sleep(1)

        if panel("/api/auth_state", method="GET").get("need_setup"):
            panel("/api/setup", {"password": PANEL_PWD})
        t = panel("/api/login", {"password": PANEL_PWD})["token"]

        # 配置：管理员=10001，允许删除
        core_cfg = json.load(open(r"..\qqbot-framework\QQBotData\config.json", encoding="utf-8"))
        core_cfg.setdefault("permissions", {})["admins"] = [str(ADMIN)]
        json.dump(core_cfg, open(r"..\qqbot-framework\QQBotData\config.json", "w",
                                 encoding="utf-8"), ensure_ascii=False, indent=2)
        panel("/api/modules/system_kit/config",
              {"config": {"enabled": True, "cmd_prefix": "系统", "allow_delete": True}}, token=t)

        async def say(uid, text):
            ev = {"post_type": "message", "message_type": "private", "user_id": uid,
                  "raw_message": text, "sender": {"nickname": str(uid)}}
            req = urllib.request.Request(
                BASE + f"/onebot/v11/events?access_token={OB_TOKEN}", method="POST")
            req.add_header("Content-Type", "application/json")
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: urllib.request.urlopen(req, json.dumps(ev).encode(), timeout=8).read())

        async def wait(contains, timeout=15):
            for _ in range(timeout * 2):
                for pkt in received:
                    if contains in json.dumps(pkt, ensure_ascii=False):
                        return True
                await asyncio.sleep(0.5)
            return False

        def last():
            return json.dumps(received[-1], ensure_ascii=False) if received else "(无)"

        import shutil
        shutil.rmtree(TMP, ignore_errors=True)

        # 1. 非管理员被拒
        await say(NON_ADMIN, "系统状态")
        ok = await wait("仅管理员可用")
        results.append(("非管理员被拒绝", ok, last()))

        # 2. 系统状态
        await say(ADMIN, "系统状态")
        ok = await wait("CPU:")
        results.append(("系统状态", ok, last()))

        # 3. 建夹（多级）
        d = os.path.join(TMP, "a", "b")
        await say(ADMIN, f"系统建夹 {d}")
        ok = await wait(f"已创建文件夹 {d}".replace("\\", "\\\\"))
        results.append(("创建文件夹", ok and os.path.isdir(d), last()))

        # 4. 写入文件
        f = os.path.join(d, "hello.txt")
        await say(ADMIN, f"系统写入 {f}|你好,系统工具!")
        ok = await wait(f"已写入 {f}".replace("\\", "\\\\"))
        results.append(("写入文件", ok and open(f, encoding="utf-8").read() == "你好,系统工具!", last()))

        # 5. 读取文件
        await say(ADMIN, f"系统读取 {f}")
        ok = await wait("你好,系统工具!")
        results.append(("读取文件", ok, last()))

        # 6. 目录列表
        await say(ADMIN, f"系统目录 {d}")
        ok = await wait("[文件] hello.txt")
        results.append(("目录列表", ok, last()))

        # 7. 执行 PowerShell
        await say(ADMIN, "系统执行 Write-Output qqbot-shell-ok")
        ok = await wait("qqbot-shell-ok")
        results.append(("执行命令", ok, last()))

        # 8. 删除
        await say(ADMIN, f"系统删除 {TMP}")
        ok = await wait(f"已删除 {TMP}".replace("\\", "\\\\"))
        results.append(("删除文件夹", ok and not os.path.exists(TMP), last()))

        print("\n===== system_kit 测试结果 =====")
        passed = 0
        for name, ok, detail in results:
            print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  | " + detail))
            passed += ok
        print(f"{passed}/{len(results)} 通过")

        await ws.close()


asyncio.run(main())
