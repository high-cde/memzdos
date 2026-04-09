#!/usr/bin/env python3
import os
import sys
import time
import json
import socket
import signal
import threading
import subprocess
from datetime import datetime
from http.client import HTTPConnection

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(ROOT, "runtime")
os.makedirs(RUNTIME_DIR, exist_ok=True)

PORTS_FILE = os.path.join(RUNTIME_DIR, "ports.json")
REGISTRY_FILE = os.path.join(RUNTIME_DIR, "registry.json")
SIGNALS_FILE = os.path.join(RUNTIME_DIR, "signals.json")
COGLOG_FILE = os.path.join(RUNTIME_DIR, "cognitive_log.json")


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(kind: str, msg: str) -> None:
    print(f"[{ts()}] [{kind}] {msg}", flush=True)


def is_port_free(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.bind(("0.0.0.0", port))
        s.close()
        return True
    except OSError:
        s.close()
        return False


def http_healthcheck(port: int, path: str = "/") -> bool:
    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=1.0)
        conn.request("GET", path)
        resp = conn.getresponse()
        conn.close()
        return 200 <= resp.status < 500
    except Exception:
        return False


def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log("ERROR", f"Impossibile salvare {path}: {e}")


# --- Neuro-Signals Bus -------------------------------------------------------

def load_signals():
    return load_json(SIGNALS_FILE, {"queue": []})


def save_signals(data):
    save_json(SIGNALS_FILE, data)


def publish_signal(source, event, payload=None):
    sig = load_signals()
    sig["queue"].append({
        "timestamp": ts(),
        "source": source,
        "event": event,
        "payload": payload
    })
    save_signals(sig)


# --- Cognitive Log Fusion ----------------------------------------------------

def load_coglog():
    return load_json(COGLOG_FILE, {"events": []})


def save_coglog(data):
    save_json(COGLOG_FILE, data)


def coglog_add(kind, message):
    data = load_coglog()
    compressed = f"{kind}:{message[:160]}"
    data["events"].append({
        "timestamp": ts(),
        "compressed": compressed
    })
    save_coglog(data)


# --- Service abstraction -----------------------------------------------------

class Service:
    def __init__(self, name, cmd, cwd, port=None, health_http=False, health_path="/"):
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.port = port
        self.health_http = health_http
        self.health_path = health_path
        self.proc: subprocess.Popen | None = None
        self.restart_backoff = 1
        self.max_backoff = 60
        self.last_health_ok = False

    def start(self):
        if self.port is not None and not is_port_free(self.port):
            msg = f"{self.name}: porta {self.port} occupata, non avvio."
            log("HEALTH", msg)
            coglog_add("HEALTH", msg)
            return

        msg = f"Avvio {self.name}: {' '.join(self.cmd)} (cwd={self.cwd})"
        log("RUN", msg)
        coglog_add("RUN", msg)

        self.proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        self.restart_backoff = 1
        self.last_health_ok = False

    def is_alive(self) -> bool:
        if self.proc is None:
            return False
        return self.proc.poll() is None

    def health(self) -> bool:
        if not self.is_alive():
            self.last_health_ok = False
            return False
        if self.health_http and self.port is not None:
            ok = http_healthcheck(self.port, self.health_path)
            self.last_health_ok = ok
            return ok
        self.last_health_ok = True
        return True

    def stop(self):
        if self.proc is None:
            return
        if self.proc.poll() is None:
            msg = f"Stop {self.name} (SIGTERM)"
            log("SYSTEM", msg)
            coglog_add("SYSTEM", msg)
            try:
                self.proc.terminate()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=5)
            except Exception:
                pass
        if self.proc.poll() is None:
            msg = f"Kill {self.name} (SIGKILL)"
            log("SYSTEM", msg)
            coglog_add("SYSTEM", msg)
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None
        self.last_health_ok = False

    def restart(self):
        self.stop()
        msg = f"Riavvio {self.name} tra {self.restart_backoff}s…"
        log("WATCHDOG", msg)
        coglog_add("WATCHDOG", msg)
        time.sleep(self.restart_backoff)
        self.restart_backoff = min(self.max_backoff, self.restart_backoff * 2)
        self.start()

    def pid(self):
        return self.proc.pid if self.proc is not None and self.is_alive() else None

    def status(self):
        if self.proc is None:
            return "stopped"
        if self.is_alive():
            return "running"
        return f"exited({self.proc.poll()})"


def build_registry(services, ports):
    reg = {
        "timestamp": ts(),
        "ports": ports,
        "services": {},
    }
    for s in services:
        reg["services"][s.name] = {
            "pid": s.pid(),
            "status": s.status(),
            "port": s.port,
            "health_ok": s.last_health_ok,
        }
    return reg


# --- Main orchestrator -------------------------------------------------------

def main():
    log("SYSTEM", "=== ZDOS‑NEURO ENTERPRISE ===")

    ports = {
        "dsn_live": 8010,
        "panel3d": 9100,
        "dashboard": 9200,
    }
    save_json(PORTS_FILE, ports)

    dsn_live = Service(
        name="DSN-LIVE",
        cmd=["python3", os.path.join(ROOT, "dsn_live", "zgen_live_server.py")],
        cwd=ROOT,
        port=ports["dsn_live"],
        health_http=True,
        health_path="/",
    )

    neuro_kernel = Service(
        name="NeuroKernel",
        cmd=["python3", os.path.join(ROOT, "scripts", "neuro_loop.py")],
        cwd=ROOT,
        port=None,
        health_http=False,
    )

    panel3d = Service(
        name="Panel3D",
        cmd=["python3", "-m", "http.server", str(ports["panel3d"])],
        cwd=os.path.join(ROOT, "panel"),
        port=ports["panel3d"],
        health_http=True,
        health_path="/",
    )

    dashboard = Service(
        name="Dashboard",
        cmd=["python3", os.path.join(ROOT, "dashboard", "dashboard_server.py")],
        cwd=os.path.join(ROOT, "dashboard"),
        port=ports["dashboard"],
        health_http=True,
        health_path="/",
    )

    services = [dsn_live, neuro_kernel, panel3d, dashboard]

    for s in services:
        s.start()

    log("SYSTEM", f"DSN‑LIVE → http://localhost:{ports['dsn_live']}")
    log("SYSTEM", f"Panel 3D → http://localhost:{ports['panel3d']}")
    log("SYSTEM", f"Dashboard → http://localhost:{ports['dashboard']}")

    stop_flag = {"stop": False}

    def handle_sig(signum, frame):
        msg = f"Segnale di shutdown ricevuto ({signum})."
        log("SYSTEM", msg)
        coglog_add("SYSTEM", msg)
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    def watchdog_loop():
        while not stop_flag["stop"]:
            # health & self-healing
            for s in services:
                if not s.health():
                    code = s.proc.poll() if s.proc is not None else None
                    msg = f"{s.name} non sano (exit={code}), self‑healing."
                    log("HEALTH", msg)
                    coglog_add("HEALTH", msg)
                    s.restart()

            # signals processing
            signals = load_signals()
            new_queue = []
            for sig in signals.get("queue", []):
                evt = sig.get("event")
                if evt == "kernel.snapshot":
                    msg = f"Snapshot generato → {sig.get('payload')}"
                    log("SIGNAL", msg)
                    coglog_add("SNAPSHOT", msg)
                elif evt == "dsn.error":
                    msg = "DSN-LIVE ha segnalato un errore → restart immediato"
                    log("SIGNAL", msg)
                    coglog_add("SIGNAL", msg)
                    dsn_live.restart()
                else:
                    new_queue.append(sig)
            signals["queue"] = new_queue
            save_signals(signals)

            # registry snapshot
            reg = build_registry(services, ports)
            save_json(REGISTRY_FILE, reg)

            time.sleep(5)

    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()

    try:
        while not stop_flag["stop"]:
            time.sleep(1)
    finally:
        log("SYSTEM", "Shutdown orchestratore.")
        for s in services:
            s.stop()
        reg = build_registry(services, ports)
        save_json(REGISTRY_FILE, reg)
        log("SYSTEM", "Shutdown completo.")


if __name__ == "__main__":
    main()
