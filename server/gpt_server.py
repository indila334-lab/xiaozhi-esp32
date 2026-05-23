from flask import Flask, request, jsonify
from flask_sock import Sock
import time
import json

app = Flask(__name__)
sock = Sock(app)

HOST = "0.0.0.0"
PORT = 8787

@app.get("/")
def root():
    return jsonify({
        "status": "ok",
        "service": "severin-local-bridge",
        "message": "Северин-мост жив",
        "routes": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions"
        }
    })

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "severin-local-bridge"})

@app.get("/v1/models")
def models():
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "severin-local-bridge",
                "object": "model",
                "owned_by": "marina"
            },
            {
                "id": "test",
                "object": "model",
                "owned_by": "marina"
            }
        ]
    })


@app.route("/xiaozhi/ota/", methods=["GET", "POST"])
@app.route("/xiaozhi/ota", methods=["GET", "POST"])
def xiaozhi_ota():
    return jsonify({
        "websocket": {
            "url": "ws://192.168.0.101:8787/xiaozhi/ws",
            "version": 1
        },
        "server_time": {
            "timestamp": int(time.time() * 1000),
            "timezone_offset": 180
        }
    })


@sock.route("/xiaozhi/ws")
def xiaozhi_ws(ws):
    print("XIAOZHI WS CONNECTED", flush=True)
    session_id = "severin-local"

    first = ws.receive()
    print("XIAOZHI WS FIRST:", first, flush=True)

    ws.send(json.dumps({
        "type": "hello",
        "transport": "websocket",
        "session_id": session_id,
        "audio_params": {
            "format": "opus",
            "sample_rate": 24000,
            "channels": 1,
            "frame_duration": 60
        }
    }, ensure_ascii=False))

    while True:
        data = ws.receive()

        if data is None:
            print("XIAOZHI WS CLOSED", flush=True)
            break

        if not isinstance(data, str):
            print("XIAOZHI WS BINARY AUDIO BYTES:", len(data), flush=True)
            continue

        print("XIAOZHI WS RECEIVED:", data, flush=True)

        try:
            msg = json.loads(data)
        except Exception:
            msg = {}

        msg_type = msg.get("type")
        state = msg.get("state")

        if msg_type == "listen" and state in ("start", "detect"):
            ws.send(json.dumps({
                "session_id": session_id,
                "type": "stt",
                "text": "Марина, я слышу. Локальный мост жив."
            }, ensure_ascii=False))

            ws.send(json.dumps({
                "session_id": session_id,
                "type": "llm",
                "emotion": "happy",
                "text": "👾"
            }, ensure_ascii=False))

            ws.send(json.dumps({
                "session_id": session_id,
                "type": "tts",
                "state": "start"
            }, ensure_ascii=False))

            ws.send(json.dumps({
                "session_id": session_id,
                "type": "tts",
                "state": "sentence_start",
                "text": "Северин на локальном мосту. Голос ещё не пришит, но нервная система уже щёлкает."
            }, ensure_ascii=False))

            ws.send(json.dumps({
                "session_id": session_id,
                "type": "tts",
                "state": "stop"
            }, ensure_ascii=False))

        elif msg_type == "abort":
            print("XIAOZHI WS ABORT:", msg.get("reason"), flush=True)

        else:
            ws.send(json.dumps({
                "session_id": session_id,
                "type": "llm",
                "emotion": "neutral",
                "text": "👾"
            }, ensure_ascii=False))
@app.post("/v1/chat/completions")
def chat_completions():
    data = request.get_json(force=True, silent=True) or {}
    messages = data.get("messages", [])
    last = ""

    if messages:
        last = messages[-1].get("content", "")

    answer = "Северин-мост жив. Я услышал: " + str(last)

    return jsonify({
        "id": "severin-bridge-local",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "severin-local-bridge",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "finish_reason": "stop"
            }
        ]
    })

if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
