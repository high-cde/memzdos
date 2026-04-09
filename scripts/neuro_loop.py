import time
from pathlib import Path
from kernel.neuro_kernel import NeuroKernel

def main():
    root = Path(__file__).resolve().parents[1]
    kernel = NeuroKernel(root)
    print("[NEURO-LOOP] Starting continuous loop...")
    try:
        while True:
            result = kernel.step()
            print("[NEURO-LOOP] Path:", result["path"])
            print("[NEURO-LOOP] Snapshot:", result["snapshot"])
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("[NEURO-LOOP] Stopped by user.")

if __name__ == "__main__":
    main()
