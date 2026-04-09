#!/usr/bin/env python3
import os, sys, time, json, socket, signal, threading, subprocess
from datetime import datetime
from http.client import HTTPConnection

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(ROOT, "runtime")
os.makedirs(RUNTIME, exist_ok=True)

# Files
PORTS_FILE = os.path.join(RUNTIME, "ports_mesh.json")
REGISTRY_FILE = os.path.join(RUNTIME, "registry_mesh.json")
SIGNALS_FILE = os.path.join(RUNTIME, "signals.json")
COGLOG_FILE = os.path.join(RUNTIME, "cognitive_log.json")

# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(kind, msg):
    print(f"[{ts()}] [{kind}] {msg}", flush=True)

def load_json(path, default):
    try:
        return json.load(open(path))
    except:
        return default

def save_json(path, data):
    try:
        json.dump(data, open(path, "w"), indent=2)
    except Exception as e:
        log("ERROR", f"Impossibile salvare {path}: {e}")

# ---------------------------------------------------------
# Dynamic Port Allocator (Quantum Mesh)
# ---------------------------------------------------------

def find_free_port(start=7000, end=9999):
    for p in range(start, end):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", p))
            s.close()
            return p
        except:
            s.close()
    raise RuntimeError("Nessuna porta libera trovata")

# ---------------------------------------------------------
# Neuro-Signals Bus v2
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# Cognitive Log Fusion AAAK v3
# ---------------------------------------------------------

def load_coglog():
    return load_json(COGLOG_FILE, {"events": []})

def save_coglog(data):
    save_json(COGLOG_FILE, data)

def coglog_add(kind, message):
    data = load_coglog()
    compressed = f"{kind}:{message[:200]}"
    data["events"].append({
        "timestamp": ts(),
        "compressed": compressed
    })
    save_coglog(data)

# ---------------------------------------------------------
# Service abstraction
# ---------------------------------------------------------

class Service:
    def __init__(self, name, cmd, cwd, port=None, health_http=False, health_path="/"):
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.port = port
        self.health_http = health_http
        self.health_path = health_path
        self.proc = None
        self.restart_backoff = 1
        self.max_backoff = 60
        self.last_health_ok = False

    def start(self):
        if self.port is None:
            self.port = find_free_port()

        if not self._port_free():
            msg = f"{self.name}: porta {self.port} occupata, salto avvio."
            log("HEALTH", msg)
            coglog_add("HEALTH", msg)
            return

        msg = f"Avvio {self.name} su porta {self.port}"
        log("RUN", msg)
        coglog_add("RUN", msg)

        env = os.environ.copy()
        env["ZPORT"] = str(self.port)

        self.proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env
        )
        self.restart_backoff = 1
        self.last_health_ok = False

    def _port_free(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", self.port))
            s.close()
            return True
        except:
            s.close()
            return False

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None

    def health(self):
        if not self.is_alive():
            self.last_health_ok = False
            return False
        if self.health_http:
            try:
                conn = HTTPConnection("127.0.0.1", self.port, timeout=1)
                conn.request("GET", self.health_path)
                resp = conn.getresponse()
                conn.close()
                ok = 200 <= resp.status < 500
                self.last_health_ok = ok
                return ok
            except:
                self.last_health_ok = False
                return False
        self.last_health_ok = True
        return True

    def stop(self):
        if self.proc is None:
            return
        if self.is_alive():
            log("SYSTEM", f"Stop {self.name} (SIGTERM)")
            coglog_add("SYSTEM", f"Stop {self.name}")
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except:
                pass
        if self.is_alive():
            log("SYSTEM", f"Kill {self.name} (SIGKILL)")
            coglog_add("SYSTEM", f"Kill {self.name}")
            try:
                self.proc.kill()
            except:
                pass
        self.proc = None
        self.last_health_ok = False

    def restart(self):
        self.stop()
        msg = f"Riavvio {self.name} tra {self.restart_backoff}s"
        log("WATCHDOG", msg)
        coglog_add("WATCHDOG", msg)
        time.sleep(self.restart_backoff)
        self.restart_backoff = min(self.max_backoff, self.restart_backoff * 2)
        self.start()

    def pid(self):
        return self.proc.pid if self.is_alive() else None

    def status(self):
        if self.proc is None:
            return "stopped"
        if self.is_alive():
            return "running"
        return f"exited({self.proc.poll()})"

# ---------------------------------------------------------
# Registry (Quantum Mesh)
# ---------------------------------------------------------

def build_registry(services):
    reg = {
        "timestamp": ts(),
        "services": {}
    }
    for s in services:
        reg["services"][s.name] = {
            "pid": s.pid(),
            "status": s.status(),
            "port": s.port,
            "health_ok": s.last_health_ok,
        }
    return reg

# ---------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------

def main():
    log("SYSTEM", "=== ZDOS‑NEURO ENTERPRISE v11 – QUANTUM MESH ===")

    # Services with dynamic ports
    dsn_live = Service(
        "DSN-LIVE",
        ["python3", os.path.join(ROOT, "dsn_live", "zgen_live_server.py")],
        ROOT,
        port=None,
        health_http=True
    )

    neuro_kernel = Service(
        "NeuroKernel",
        ["python3", os.path.join(ROOT, "scripts", "neuro_loop.py")],
        ROOT
    )

    panel3d = Service(
        "Panel3D",
        ["python3", "-m", "http.server"],
        os.path.join(ROOT, "panel"),
        port=None,
        health_http=True
    )

    dashboard = Service(
        "Dashboard",
        ["python3", os.path.join(ROOT, "dashboard", "dashboard_server.py")],
        os.path.join(ROOT, "dashboard"),
        port=None,
        health_http=True
    )

    services = [dsn_live, neuro_kernel, panel3d, dashboard]

    # Start all
    for s in services:
        s.start()

    stop_flag = {"stop": False}

    def handle_sig(signum, frame):
        log("SYSTEM", f"Segnale {signum} ricevuto → shutdown mesh")
        stop_flag["stop"] = True

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    def watchdog():
        while not stop_flag["stop"]:
            # Health
            for s in services:
                if not s.health():
                    log("HEALTH", f"{s.name} non sano → restart")
                    coglog_add("HEALTH", f"{s.name} non sano")
                    s.restart()

            # Signals
            sigs = load_signals()
            newq = []
            for sig in sigs["queue"]:
                evt = sig["event"]
                if evt == "kernel.snapshot":
                    coglog_add("SNAPSHOT", f"{sig['payload']}")
                else:
                    newq.append(sig)
            sigs["queue"] = newq
            save_signals(sigs)

            # Registry
            reg = build_registry(services)
            save_json(REGISTRY_FILE, reg)

            time.sleep(5)

    threading.Thread(target=watchdog, daemon=True).start()

    try:
        while not stop_flag["stop"]:
            time.sleep(1)
    finally:
        for s in services:
            s.stop()
        save_json(REGISTRY_FILE, build_registry(services))
        log("SYSTEM", "Shutdown completo.")

if __name__ == "__main__":
    main()
