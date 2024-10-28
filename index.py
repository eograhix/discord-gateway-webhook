from flask import Flask, request, jsonify, abort, Response
import nacl.signing
import nacl.exceptions
import os, json

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")


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


@app.route('/webhook', methods=['POST'])
def webhook():
        if request.method != 'POST':
            return Response('invalid method', status=405)
    
        signature = request.headers.get('X-Signature-Ed25519')
        timestamp = request.headers.get('X-Signature-Timestamp')
        body = request.data.decode("utf-8")
    
        if not verify_signature(signature, timestamp, body):
            abort(401, 'Missing required headers')
            
        data = request.get_json()
        event_type = data.get('type')
        event = data.get('event')


        if event_type == 0:  # PING
            return Response(status=204)
        
        elif event_type == 1:  # Webhook Event
            if event['type'] == 'APPLICATION_AUTHORIZED':
                integration_type = event['data'].get('integration_type')
                if integration_type == 0:
                    # Guild Install
                    pass
                elif integration_type == 1:
                    # User Install
                    pass
                save_event("Unknown event type received", request.json)
            elif event['type'] == 'ENTITLEMENT_CREATE':
                pass
            elif event['type'] == 'QUEST_USER_ENROLLMENT':
                pass
            return Response(status=204)
        else:
            return Response('invalid request', status=400)




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
