import paho.mqtt.client as mqtt
import time
import json

MQTT_BROKER = "mqtt.dsic.upv.es"
MQTT_PORT = 1883
MQTT_TOPIC = "incubadora/esp3"

def enviar_mensaje_mqtt():
    client = mqtt.Client(callback_api_version = mqtt.CallbackAPIVersion.VERSION2)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        client.loop_start()
        
        payload = json.dumps({"distancia": 10})
        
        client.publish(MQTT_TOPIC, payload)
        
        time.sleep(1)
        
    except Exception as e:
        raise Exception("error")
        
    finally:
        client.loop_stop()
        client.disconnect()
        print("[MQTT] Desconexión realizada.")

if __name__ == "__main__":
    enviar_mensaje_mqtt()
