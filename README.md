# Time Range Sort Microservice

## What it does

Returns objects whose chosen date field falls within an inclusive date range,
sorted from earliest to latest.

## How to run it

Use Python 3.10 or newer. Open a terminal in this folder:

```text
python -m pip install -r requirements.txt
python microservice.py
```

Leave the server running. In a second terminal in the same folder:

```text
python test_client.py
```

## Communication contract

ZeroMQ REQ/REP over TCP, with JSON messages. The server binds to
`tcp://127.0.0.1:5554`. A client connects using a REQ socket and alternates one
request with one reply. Start the server first. No direct function imports,
external API, database, or tracker-specific data types are needed.

### Requesting data

Every request is a JSON object with these required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `action` | string | Exactly `"range"` |
| `items` | array of objects | Every object must contain the chosen date field |
| `field` | nonempty string | Name of the date field in each object |
| `start` | string | Inclusive start date, exactly `YYYY-MM-DD` |
| `end` | string | Inclusive end date, exactly `YYYY-MM-DD` |

Dates must be real calendar dates. The start must be on or before the end.
Timestamps and alternate date formats are rejected. An empty `items` array is
valid and returns an empty `results` array.

Complete Python example, including the request call and receive call:

```python
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 3000)
socket.setsockopt(zmq.SNDTIMEO, 3000)
socket.setsockopt(zmq.LINGER, 0)
socket.connect("tcp://127.0.0.1:5554")
request = {
    "action": "range",
    "items": [{"id": 1, "date": "2026-10-10"},
              {"id": 2, "date": "2026-10-20"}],
    "field": "date",
    "start": "2026-10-05",
    "end": "2026-10-15",
}
try:
    socket.send_json(request)       # REQUEST: one JSON message
    reply = socket.recv_json()      # RECEIVE: one JSON message
    if reply["status"] == "ok":
        print(reply["results"])
    else:
        print(reply["message"])
except zmq.Again:
    print("Timed out. Check that the server is running.")
finally:
    socket.close()
    context.term()
```

After a timeout, close the REQ socket and create a new one before retrying;
REQ sockets require alternating send and receive operations.

### Receiving data

Use `socket.recv_json()` once after each `socket.send_json(request)`. It blocks
until the reply arrives or the configured timeout expires. Do not add a second
receive for the same request.

Successful response for the example above:

```json
{"status": "ok", "results": [{"id": 1, "date": "2026-10-10"}]}
```

No matches: `{"status": "ok", "results": []}`.

Invalid input produces `status: "error"` and a descriptive `message` instead
of results. This includes a wrong action, invalid array or field, missing date
field, invalid item/start/end date, or reversed range. The service replies with
an error and remains available for the next request.

```json
{"status": "error", "message": "start must be on or before end"}
```

## UML sequence diagram
<img width="1600" height="1000" alt="sequence" src="https://github.com/user-attachments/assets/c5c2c8ad-a1f2-4a85-b5d9-fc653b1ca0ae" />

The diagram's arrows represent network messages, not direct calls between
programs. The server loops back to receive another request after every reply.

## Files

- `microservice.py`: REP server, validation, inclusive filtering, stable sorting.
- `test_client.py`: Independent REQ client with success and error examples.
- `requirements.txt`: Python ZeroMQ dependency.
