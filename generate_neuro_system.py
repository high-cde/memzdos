from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip())

def main():
    print("[ZDOS-NEURO] CLEAN REBUILD")

    # -------------------------
    # DSN-LIVE SERVER (CLEAN)
    # -------------------------
    write(
        ROOT / "dsn_live" / "zgen_live_server.py",
        """
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
        """
    )

    # -------------------------
    # PANEL 3D
    # -------------------------
    write(
        ROOT / "panel" / "index.html",
        """
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>ZDOS-NEURO Panel</title>
          <style>body{margin:0;background:#000;color:#0f0;font-family:monospace}</style>
        </head>
        <body>
          <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
          <script src="app.js"></script>
        </body>
        </html>
        """
    )

    write(
        ROOT / "panel" / "app.js",
        """
        const scene=new THREE.Scene();
        const camera=new THREE.PerspectiveCamera(60,window.innerWidth/window.innerHeight,0.1,1000);
        const renderer=new THREE.WebGLRenderer({antialias:true});
        renderer.setSize(window.innerWidth,window.innerHeight);
        document.body.appendChild(renderer.domElement);
        camera.position.z=30;

        const nodes={};
        const ws=new WebSocket("ws://"+location.hostname+":8000/ws");

        ws.onmessage=(event)=>{
            const data=JSON.parse(event.data);
            if(!data.viz3d) return;
            data.viz3d.nodes.forEach(n=>{
                if(!nodes[n.id]){
                    const g=new THREE.SphereGeometry(0.4,16,16);
                    const m=new THREE.MeshBasicMaterial({color:0x00ff00});
                    const mesh=new THREE.Mesh(g,m);
                    mesh.position.set(n.x,n.y,n.z);
                    scene.add(mesh);
                    nodes[n.id]=mesh;
                }
            });
            ws.send("step");
        };

        function animate(){
            requestAnimationFrame(animate);
            scene.rotation.y+=0.002;
            renderer.render(scene,camera);
        }
        animate();
        """
    )

    # -------------------------
    # AUTOBUILD (CLEAN)
    # -------------------------
    write(
        ROOT / "scripts" / "autobuild.py",
        """
        import time, subprocess
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]

        def run(cmd):
            print("[AUTOBUILD] Running:", " ".join(cmd))
            return subprocess.run(cmd, cwd=ROOT)

        def run_server():
            return subprocess.Popen(["python", "dsn_live/zgen_live_server.py"], cwd=ROOT)

        def main():
            print("[AUTOBUILD] CLEAN MASTER START")
            run(["python", "generate_neuro_system.py"])
            proc = run_server()
            try:
                while True:
                    time.sleep(1)
                    if proc.poll() is not None:
                        print("[AUTOBUILD] Restarting server...")
                        proc = run_server()
            except KeyboardInterrupt:
                proc.terminate()

        if __name__ == "__main__":
            main()
        """
    )

    print("[ZDOS-NEURO] CLEAN SYSTEM READY")

if __name__ == "__main__":
    main()
