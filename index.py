from flask import Flask, request, jsonify, abort
import nacl.signing
import nacl.exceptions
import os, json


def save_event(event_type, log_entry):
    global msg
    msg.append({"event_type": event_type, "log_entry": log_entry})


def verify_signature(signature, timestamp, body):
    try:
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
        return True
    except nacl.exceptions.BadSignatureError:
        return False


app = Flask(__name__)


msg = []


DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")


@app.route('/webhook', methods=['POST'])
def webhook():
    # Handle the PING event
    if request.json and request.json.get('type') == 0:  # Type 0 = PING
        save_event("PING", request.json)
        return '', 204

    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    body = request.data.decode("utf-8")

    if not verify_signature(signature, timestamp, body):
        abort(401, 'Missing required headers')

    event = request.json.get("event", {})
    event_type = event.get("type")

    save_event("Unknown event type received", request.json)
    return jsonify({'status': 'Event received'}), 200




@app.route('/get_events', methods=['GET'])
def get_events():
        return jsonify(msg), 200

@app.route('/clear', methods=['GET'])
def clear_events():
        global msg
        msg = []
        return 204


if __name__ == '__main__':
    app.run(port=5000)
