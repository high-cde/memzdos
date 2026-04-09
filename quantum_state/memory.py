from pathlib import Path
import json
from datetime import datetime

class QuantumMemory:
    def __init__(self, root: Path):
        self.snap_dir = root / "docs" / "snapshots"
        self.snap_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, fingerprint: dict, state: str):
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        snap = {
            "timestamp": ts,
            "fingerprint": fingerprint,
            "state": state,
        }
        path = self.snap_dir / f"snapshot_{ts}.json"
        path.write_text(json.dumps(snap, indent=2))
        return path

    def latest(self):
        snaps = sorted(self.snap_dir.glob("snapshot_*.json"))
        if not snaps:
            return None
        return json.loads(snaps[-1].read_text())
