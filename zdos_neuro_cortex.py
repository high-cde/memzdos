from zdos_neuro_cortex_cyber import CyberCortex, CyberSignal, CyberSignalType
from typing import Any, Dict
from zdos_neuro_router import NeuroRouter


class CortexUnified:
    self.cyber = CyberCortex()
    """
    CORTEX PRINCIPALE ZDOS‑NEURO
    - riceve segnali
    - li classifica
    - li instrada ai moduli specializzati
    - mantiene coerenza cognitiva dell'organismo
    """

    def __init__(self):
        self.router = NeuroRouter()

        # I moduli specializzati (es. CyberCortex)
        # verranno collegati automaticamente dall'autobuild.
        pass

    def ingest(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Punto di ingresso generale del CORTEX.
        Ogni segnale deve avere:
        - domain
        - payload
        - context
        """
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
