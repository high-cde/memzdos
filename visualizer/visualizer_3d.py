def to_3d_payload(graph, activity: dict, state: str):
    nodes = []
    for i, n in enumerate(graph.nodes):
        nodes.append({
            "id": n,
            "x": i % 10,
            "y": (i // 10) % 10,
            "z": i // 100,
            "activity": activity.get(n, 0.0),
        })
    return {
        "nodes": nodes,
        "quantum_state": state,
    }
