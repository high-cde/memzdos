#!/usr/bin/env python3
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(ROOT, "runtime")

def load(name):
    path = os.path.join(RUNTIME_DIR, name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            data = {
                "registry": load("registry.json"),
                "signals": load("signals.json"),
                "cognitive_log": load("cognitive_log.json"),
            }
            body = json.dumps(data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

def run():
    server = HTTPServer(("0.0.0.0", 9200), Handler)
    print("Dashboard → http://localhost:9200")
    server.serve_forever()

if __name__ == "__main__":
    run()
