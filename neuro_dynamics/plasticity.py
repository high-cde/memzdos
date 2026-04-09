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
