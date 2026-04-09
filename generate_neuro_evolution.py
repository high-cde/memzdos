from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parent

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip())

def main():
    print("[ZDOS-NEURO] Evolution starting from", ROOT)

    # plasticity
    write(
        ROOT / "neuro_dynamics" / "plasticity.py",
        """
        class SynapticPlasticity:
            def __init__(self, graph, lr: float = 0.1, decay: float = 0.01):
                self.graph = graph
                self.lr = lr
                self.decay = decay
                if not hasattr(self.graph, "weights"):
                    self.graph.weights = {}

            def reinforce(self, path):
                for i in range(len(path) - 1):
                    edge = (path[i], path[i+1])
                    self.graph.weights[edge] = self.graph.weights.get(edge, 0.0) + self.lr

            def decay_all(self):
                for edge in list(self.graph.weights.keys()):
                    self.graph.weights[edge] *= (1.0 - self.decay)
                    if self.graph.weights[edge] < 1e-6:
                        del self.graph.weights[edge]
        """
    )

    # quantum memory
    write(
        ROOT / "quantum_state" / "memory.py",
        """
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
        """
    )

    # 3D visualizer
    write(
        ROOT / "visualizer" / "visualizer_3d.py",
        """
        def to_3d_payload(graph, activity: dict, state: str):
            nodes = []
            for i, n in enumerate(graph.nodes):
                nodes.append({
                    "id": n,
                    "x": i % 10,
                    "y": (i // 10) % 10,
                    "z": i // 100,
                    "activity": activity.get(n, 0.0),
                })
            return {
                "nodes": nodes,
                "quantum_state": state,
            }
        """
    )

    # unified neuro-kernel
    write(
        ROOT / "kernel" / "neuro_kernel.py",
        """
        from pathlib import Path
        from ingest import zgen_flywire_ingest_lite as ingest_mod
        from router import graph as graph_mod
        from router import router as router_mod
        from router import aak_quantum as quantum_mod
        from dsn_core import dsn_core_flyrouter as dsn_core_mod
        from neuro_io.neuro_io import NeuroIO
        from neuro_dynamics.neuro_dynamics import NeuroDynamics
        from neuro_dynamics.plasticity import SynapticPlasticity
        from quantum_state.quantum_state import QuantumState
        from quantum_state.memory import QuantumMemory
        from visualizer.visualizer import render
        from visualizer.visualizer_3d import to_3d_payload

        class NeuroKernel:
            def __init__(self, root: Path):
                self.root = root
                self.neurons, self.synapses = ingest_mod.load_flywire_dataset(
                    root / "ingest" / "flywire_neurons.tsv",
                    root / "ingest" / "flywire_synapses.tsv",
                )
                self.graph = graph_mod.build_graph(self.neurons, self.synapses)
                self.fingerprint = quantum_mod.quantum_compress_graph(self.graph)
                self.qstate = QuantumState(self.fingerprint)
                self.qmem = QuantumMemory(root)
                self.nio = NeuroIO()
                self.ndyn = NeuroDynamics(self.graph)
                self.plast = SynapticPlasticity(self.graph)

            def step(self):
                pre = self.neurons[0]["id"]
                post = self.neurons[-1]["id"]
                path = router_mod.FlyRouter(self.graph).shortest_path(pre, post)
                if path:
                    self.plast.reinforce(path)
                    for n in path:
                        self.nio.push({"fire": n})
                        self.ndyn.fire(n)
                self.plast.decay_all()
                self.qstate.collapse({"path": path})
                snap_path = self.qmem.snapshot(self.fingerprint, self.qstate.state)
                viz2d = render(self.graph, self.ndyn.activity)
                viz3d = to_3d_payload(self.graph, self.ndyn.activity, self.qstate.state)
                return {
                    "path": path,
                    "snapshot": str(snap_path),
                    "viz2d": viz2d,
                    "viz3d": viz3d,
                    "weights": getattr(self.graph, "weights", {}),
                }

        def main():
            root = Path(__file__).resolve().parents[1]
            kernel = NeuroKernel(root)
            result = kernel.step()
            print("[NEURO-KERNEL] Path:", result["path"])
            print("[NEURO-KERNEL] Snapshot:", result["snapshot"])
            print("[NEURO-KERNEL] Quantum state:", result["viz3d"]["quantum_state"])
            print("[NEURO-KERNEL] Weights (first 5):", list(result["weights"].items())[:5])

        if __name__ == "__main__":
            main()
        """
    )

    # README append
    readme = ROOT / "README.md"
    if readme.exists():
        extra = textwrap.dedent(
            """
            ## Evoluzione Neuro-Computazionale

            Moduli aggiunti:
            - neuro_dynamics/plasticity.py  → plasticità sinaptica
            - quantum_state/memory.py       → memoria quantica a lungo termine
            - visualizer/visualizer_3d.py   → payload 3D
            - kernel/neuro_kernel.py        → kernel unificato

            Per eseguire il kernel:

            ```bash
            python kernel/neuro_kernel.py
            ```
            """
        )
        readme.write_text(readme.read_text().rstrip() + "\n\n" + extra + "\n")

    print("[ZDOS-NEURO] Evolution complete.")

if __name__ == "__main__":
    main()
