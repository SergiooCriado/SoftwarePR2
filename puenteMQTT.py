import paho.mqtt.client as mqtt
import psycopg
import json
from datetime import datetime

# --- Base de datos---

DB_PARAMS = {
    "dbname": "incubadora_db",
    "user": "postgres",
    "password": "postgres", 
    "host": "localhost",
    "port": "5432"
}

# --- Parámetros seguridad (ejemplo) ---

CONFIG_CONTROL = {
    "esp1": {"co2_limite": 800, "o2_min": 19},
    "esp2": {"temp_max": 38.5,}, 
    "esp3": {"vibe_max": 2.0}
}

# MQTTX

MQTT_USER = "giirob"
MQTT_PASS = "UPV2024"
MQTT_BROKER = "mqtt.dsic.upv.es" 
MQTT_PORT = 1883

def guardar_en_db(topic, payload):
    try:
        # Extraemos el ID del dispositivo (ej: "incubadora/esp2" -> "esp2")
        partes_topic = topic.split('/')
        dispositivo = partes_topic[1] 
        datos = json.loads(payload)
        
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                
                # El bucle FOR recorre cada mensaje JSON

                for parametro, valor in datos.items():

                    # Guardar datos lectura
                    cur.execute(
                        "INSERT INTO incubadora.lecturas_sensores (dispositivo, tipo_parametro, valor) VALUES (%s, %s, %s)",
                        (dispositivo, parametro, valor)
                    )

                    if dispositivo == "esp2" and parametro == "presencia" and valor == 1:
                        cur.execute(
                            "INSERT INTO incubadora.lecturas_sensores (dispositivo, tipo_parametro, valor) VALUES (%s, %s, %s)",
                            (dispositivo, parametro, valor)
                        )
                        print(f"! PRESENCIA DE STACK !")
                    
                    # Boton emergencia
                    elif dispositivo == "esp2" and parametro == "boton" and valor == 1:
                        cur.execute(
                            "INSERT INTO incubadora.incidencias (nivel_prioridad, descripcion, estado_robot) VALUES (%s, %s, %s)",
                            ("CRÍTICO", "BOTÓN DE EMERGENCIA PULSADO", "STOP")
                        )
                        print("!!! EMERGENCIA: PARADA SOLICITADA !!!")

                    # Co2 elevado
                    elif dispositivo == "esp1" and parametro == "co2" and valor > CONFIG_CONTROL["esp1"]["co2_limite"]:
                        cur.execute(
                            "INSERT INTO incubadora.incidencias (nivel_prioridad, descripcion, estado_robot) VALUES (%s, %s, %s)",
                            ("ADVERTENCIA", f"CO2 elevado: {valor}ppm", "OPERATIVO")
                        )

                    # Oxígeno bajo
                    elif dispositivo == "esp1" and parametro == "o2" and valor < CONFIG_CONTROL["esp1"]["o2_min"]:
                        cur.execute(
                            "INSERT INTO incubadora.incidencias (nivel_prioridad, descripcion, estado_robot) VALUES (%s, %s, %s)",
                            ("ADVERTENCIA", f"O2 bajo: {valor}%", "OPERATIVO")
                        )

                    # Temperatura alta
                    elif dispositivo == "esp2" and parametro == "temperatura" and valor > CONFIG_CONTROL["esp2"]["temp_max"]:
                        cur.execute(
                            "INSERT INTO incubadora.incidencias (nivel_prioridad, descripcion, estado_robot) VALUES (%s, %s, %s)",
                            ("ADVERTENCIA", f"Exceso de calor: {valor}°C", "OPERATIVO")
                        )

                    # Vibración muy alta
                    elif dispositivo == "esp3" and parametro == "vibracion" and valor > CONFIG_CONTROL["esp3"]["vibe_max"]:
                        cur.execute(
                            "INSERT INTO incubadora.incidencias (nivel_prioridad, descripcion, estado_robot) VALUES (%s, %s, %s)",
                            ("ADVERTENCIA", f"Vibración base robot: {valor}G", "OPERATIVO")
                        )
                
                # Guardar cambios
                conn.commit()
                print(f"Datos de {dispositivo} procesados correctamente.")

    except Exception as e:
        print(f"Error procesando mensaje: {e}")

# --- 3. CONFIGURACIÓN MQTT ---

def on_message(client, userdata, msg):
    guardar_en_db(msg.topic, msg.payload)

client = mqtt.Client()
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT)
client.subscribe("incubadora/#")

print("Servidor de la incubadora escuchando MQTT...")
client.loop_forever()
