from flask import Flask, request, jsonify
import time

app = Flask(__name__)

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
