import time, json

def event_stream(neuro_io, quantum_state):
    while True:
        event = neuro_io.pull()
        if event is not None:
            quantum_state.collapse(event)
            yield json.dumps({"event": event, "state": quantum_state.state})
        time.sleep(0.1)
