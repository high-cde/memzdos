from zdos_neuro_cortex_cyber import CyberCortex, CyberSignal, CyberSignalType
from typing import Any, Dict
from zdos_neuro_router import NeuroRouter
from zdos_neuro_quantum_router import QuantumRouter


class CortexUnified:
    self.cyber = CyberCortex()
    """
    CORTEX PRINCIPALE ZDOS‑NEURO
    """

    def __init__(self):
        self.router = NeuroRouter()
        self.qrouter = QuantumRouter()

        # Moduli specializzati (patchati automaticamente)
        pass

    def ingest(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Punto di ingresso generale del CORTEX.
        """
        # Quantum Router → fallback Router
        out = self.qrouter.route(self, signal)
        if out.get("status") != "unhandled":
            return out

        return self.router.dispatch(self, signal)

    # Routing CyberCortex
    def route_cyber(self, signal):
        if getattr(signal, "domain", None) == "cybersecurity":
            return self.cyber.ingest_signal(
                CyberSignal(
                    type=signal["payload"].get("type", CyberSignalType.THREAT_INTEL),
                    payload=signal["payload"],
                    context=signal["context"]
                )
            )
        return None
