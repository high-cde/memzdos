class NeuroDynamics:
    def __init__(self, graph):
        self.graph = graph
        self.activity = {node: 0 for node in graph.nodes}

    def fire(self, node):
        if node not in self.activity:
            return
        self.activity[node] += 1
        for target in self.graph.edges.get(node, []):
            self.activity[target] = self.activity.get(target, 0) + 0.5
