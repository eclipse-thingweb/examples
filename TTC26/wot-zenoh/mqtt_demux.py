import json
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 8883
SUBSCRIBE_TOPIC = "application/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected successfully to {BROKER}:{PORT}")
        client.subscribe(SUBSCRIBE_TOPIC)
        print(f"Subscribed to {SUBSCRIBE_TOPIC}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # Extract required metadata
        device_info = payload.get("deviceInfo", {})
        app_id = device_info.get("applicationId")
        dev_eui = device_info.get("devEui")
        data_object = payload.get("object", {})

        if not all([app_id, dev_eui, data_object]):
            return 
            
        for key, value in data_object.items():
            new_topic = f"application/{app_id}/device/{dev_eui}/event/up/{key}"
            pub_val = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            
            client.publish(new_topic, pub_val)
            print(f"Published: {new_topic} -> {pub_val}")

    except json.JSONDecodeError:
        print("Received non-JSON payload")
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()