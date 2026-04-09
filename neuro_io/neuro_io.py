class NeuroIO:
    def __init__(self):
        self.events = []

    def push(self, event):
        self.events.append(event)

    def pull(self):
        if not self.events:
            return None
        return self.events.pop(0)
