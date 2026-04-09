class QuantumState:
    def __init__(self, fingerprint: dict):
        self.state = fingerprint.get("signature", "")

    def collapse(self, event):
        self.state = hex(abs(hash(self.state + str(event))))[2:18]
