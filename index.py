from flask import Flask, request, jsonify, abort, Response
import nacl.signing
import nacl.exceptions
import os, json, requests, aiohttp

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def get_app_data(app_id):
    url = f"https://discord.com/api/v9/applications/{app_id}/rpc"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None  # or handle errors as needed


def send_webhook_message(user_id, user_name, user_globalName, user_avatar, current_date):

    webhook_data = {
        "username": app_data[0]['name'],
        "avatar_url": f"https://cdn.discordapp.com/app-icons/{app_data[0]['id']}/{app_data[0]['icon']}",
        "embeds": [
            {
                "title": "BOT ADDED",
                "description": f"the bot has been added as an integrated app",
                "color": 0x614fff,
                "fields": [
                    {"name": "User ID:", "value": str(user_id), "inline": False},
                    {"name": "User Name:", "value": f"{user_name}", "inline": False},
                    {"name": "Pseudo:", "value": f"{user_globalName}", "inline": False},
                    
                ],
                "thumbnail": {"url": user_avatar+".gif"},
                                "footer": {"text": f"Date: {current_date}"}
            }
        ]
    }
    
    response = requests.post(WEBHOOK_URL, json=webhook_data)
    
    if response.status_code != 204:
        print(f"Failed to send webhook: {response.status_code} - {response.text}")


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
app_data = []

@app.route('/webhook', methods=['POST'])
async def webhook():
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
                    #save_event("Guild Install", request.json)
                    # Guild Install
                    pass
                elif integration_type == 1:
                    # User Install
                    save_event("User Install", request.json)
                    user = event['data']['user']
                    user_id = user['id']
                    user_name = user['username']
                    user_globalName = user['global_name']
                    user_avatar = f"https://cdn.discordapp.com/avatars/{user_id}/{user['avatar']}"
                    current_date = event['timestamp'] #i need to sleep :skull:

                    global app_data
                    if not app_data:
                        r_data = await get_app_data(data.get('application_id'))
                        app_data.append(r_data)
                        
                    send_webhook_message(user_id, user_name, user_globalName, user_avatar, current_date)
                    

                    pass
            elif event['type'] == 'ENTITLEMENT_CREATE':
                pass
            elif event['type'] == 'QUEST_USER_ENROLLMENT':
                pass
            return Response(status=204)
        else:
            return Response('invalid request', status=400)




@app.route('/get_events', methods=['GET'])
async def get_events():
        return jsonify(msg), 200

from flask import Response

@app.route('/clear', methods=['GET'])
async def clear_events():
    global msg, app_data
    msg, app_data = [], []

    return Response(status=204)



@app.route('/app_data', methods=['GET'])
async def return_app_data():
        return jsonify(app_data), 200


if __name__ == '__main__':
    app.run(port=5000)
