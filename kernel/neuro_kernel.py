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
