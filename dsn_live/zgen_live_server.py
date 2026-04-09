import json
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, FileResponse
from starlette.routing import Route, WebSocketRoute
from starlette.endpoints import WebSocketEndpoint
import uvicorn

from kernel.neuro_kernel import NeuroKernel

root = Path(__file__).resolve().parents[1]
kernel = NeuroKernel(root)

async def homepage(request):
    return PlainTextResponse("ZDOS-NEURO DSN-LIVE v2 - WebSocket at /ws")

async def panel(request):
    return FileResponse(root / "panel" / "index.html")

async def panel_js(request):
    return FileResponse(root / "panel" / "app.js")

class NeuroStream(WebSocketEndpoint):
    encoding = "text"
    async def on_connect(self, websocket):
        await websocket.accept()
        await websocket.send_text(json.dumps({"status": "connected"}))
    async def on_receive(self, websocket, data):
        result = kernel.step()
        await websocket.send_text(json.dumps(result))
    async def on_disconnect(self, websocket, close_code):
        pass

app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/panel", panel),
        Route("/panel/app.js", panel_js),
        WebSocketRoute("/ws", NeuroStream),
    ]
)

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
