def render(graph, activity: dict):
    return {
        "nodes": list(graph.nodes),
        "activity": activity,
    }
