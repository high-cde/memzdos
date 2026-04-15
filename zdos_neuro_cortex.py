from zdos_neuro_cortex_cyber import CyberCortex, CyberSignal, CyberSignalType
from typing import Any, Dict


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
        # I moduli specializzati (es. CyberCortex) verranno collegati automaticamente
        # dall'autobuild quantistico.
        pass

    def ingest(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Punto di ingresso generale del CORTEX.
        Ogni segnale deve avere:
        - domain
        - payload
        - context
        """
        domain = signal.get("domain")

        # Routing CyberCortex (aggiunto automaticamente dall'autobuild)
        if hasattr(self, "route_cyber"):
            out = self.route_cyber(signal)
            if out is not None:
                return out

        return {
            "status": "unhandled",
            "domain": domain,
            "message": "Nessun modulo ha gestito questo segnale."
        }

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
