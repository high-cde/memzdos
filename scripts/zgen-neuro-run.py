from pathlib import Path
from ingest import zgen_flywire_ingest_lite as ingest_mod
from router import graph as graph_mod
from router import router as router_mod
from router import aak_quantum as quantum_mod
from dsn_core import dsn_core_flyrouter as dsn_core_mod
from neuro_io.neuro_io import NeuroIO
from neuro_dynamics.neuro_dynamics import NeuroDynamics
from quantum_state.quantum_state import QuantumState
from visualizer.visualizer import render

ROOT = Path(__file__).resolve().parents[1]

def main():
    neurons, synapses = ingest_mod.load_flywire_dataset(
        ROOT / "ingest" / "flywire_neurons.tsv",
        ROOT / "ingest" / "flywire_synapses.tsv",
    )
    g = graph_mod.build_graph(neurons, synapses)
    fp = quantum_mod.quantum_compress_graph(g)
    qs = QuantumState(fp)
    nio = NeuroIO()
    nd = NeuroDynamics(g)

    for n in [neurons[0]["id"], neurons[-1]["id"]]:
        nio.push({"fire": n})
        nd.fire(n)

    viz = render(g, nd.activity)
    print("[ZDOS-NEURO] Quantum fingerprint:", fp)
    print("[ZDOS-NEURO] Sample activity (first 5):", list(viz["activity"].items())[:5])

if __name__ == "__main__":
    main()
