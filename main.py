import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import websockets

TOKEN = os.environ.get("DISCORD_TOKEN", "")
STATUS = "online"
CUSTOM_STATUS = ""
USE_EMOJI = False

if not TOKEN:
    print("DISCORD_TOKEN environment variable is not set!")
    exit(1)

headers = {"Authorization": TOKEN}
r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
if r.status_code != 200:
    print("Invalid token!")
    exit()

user = r.json()
print(f"Logged in as {user['username']} ({user['id']})!")

activity = {"name": "Custom Status", "type": 4, "state": CUSTOM_STATUS, "id": "custom"}

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"alive")
    def log_message(self, format, *args):
        pass

def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    print(f"Ping server running on port {port}")
    server.serve_forever()

async def discord_gateway():
    uri = "wss://gateway.discord.gg/?v=10&encoding=json"
    async with websockets.connect(uri, max_size=10 * 1024 * 1024) as ws:
        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]
        async def heartbeat():
            while True:
                await asyncio.sleep(heartbeat_interval / 1000)
                await ws.send(json.dumps({"op": 1, "d": None}))
        asyncio.create_task(heartbeat())
        identify = {"op": 2, "d": {"token": TOKEN, "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"}, "presence": {"status": STATUS, "afk": False, "activities": [activity]}}}
        await ws.send(json.dumps(identify))
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("op") == 11:
                    pass
            except Exception as e:
                print("Connection lost, reconnecting...", e)
                break

async def main():
    while True:
        await discord_gateway()
        await asyncio.sleep(5)

threading.Thread(target=start_http_server, daemon=True).start()
asyncio.run(main())
