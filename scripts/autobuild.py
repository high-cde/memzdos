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
