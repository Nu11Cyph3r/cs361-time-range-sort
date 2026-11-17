"""Time Range Sort microservice. ZeroMQ REQ/REP, JSON, TCP port 5554."""
from datetime import date
import json
import re
import zmq

PORT = 5554


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("use a real date in YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("use a real date in YYYY-MM-DD format") from None


def handle_request(request):
    if not isinstance(request, dict) or request.get("action") != "range":
        return {"status": "error", "message": "action must be 'range'"}
    items = request.get("items")
    field = request.get("field")
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        return {"status": "error", "message": "items must be an array of objects"}
    if not isinstance(field, str) or not field:
        return {"status": "error", "message": "field must be a nonempty string"}
    try:
        start = parse_date(request.get("start"))
    except ValueError as exc:
        return {"status": "error", "message": f"start: {exc}"}
    try:
        end = parse_date(request.get("end"))
    except ValueError as exc:
        return {"status": "error", "message": f"end: {exc}"}
    if start > end:
        return {"status": "error", "message": "start must be on or before end"}
    dated = []
    for index, item in enumerate(items):
        if field not in item:
            return {"status": "error", "message": f"missing field '{field}' in item {index}"}
        try:
            item_date = parse_date(item[field])
        except ValueError as exc:
            return {"status": "error", "message": f"field '{field}' in item {index}: {exc}"}
        if start <= item_date <= end:
            dated.append((item_date, item))
    dated.sort(key=lambda pair: pair[0])
    return {"status": "ok", "results": [item for _, item in dated]}


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.LINGER, 0)
    socket.bind(f"tcp://127.0.0.1:{PORT}")
    print(f"Time Range Sort ready on tcp://127.0.0.1:{PORT}", flush=True)
    try:
        while True:
            try:
                request = socket.recv_json()
                print(f"REQUEST: {json.dumps(request, ensure_ascii=False)}", flush=True)
                response = handle_request(request)
            except Exception as exc:
                response = {"status": "error", "message": f"invalid request: {exc}"}
            print(f"RESPONSE: {json.dumps(response, ensure_ascii=False)}", flush=True)
            socket.send_json(response)
    except KeyboardInterrupt:
        print("Service stopped.")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
