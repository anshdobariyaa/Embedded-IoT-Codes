import network
import time
from machine import Pin
from umqtt.simple import MQTTClient
import dht

# ------------------ Configuration ------------------
WIFI_SSID = "RADHE"
WIFI_PASSWORD = "9173126511"
MQTT_SERVER = "mqtt-dashboard.com"
CLIENT_ID = "ESP32_Client"
TOPIC_PUB_TEMP = b"iotfrontier/temperature"
TOPIC_PUB_HUM = b"iotfrontier/humidity"
TOPIC_SUB = b"iotfrontier/mqtt"

# ------------------ GPIO Setup ------------------
led = Pin(2, Pin.OUT)
sensor = dht.DHT22(Pin(9))

# ------------------ WiFi Connection ------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nWiFi Connected")
    print("IP Address:", wlan.ifconfig()[0])

# ------------------ MQTT Callback ------------------
def mqtt_callback(topic, msg):
    print(f"Message Received [{topic.decode()}]: {msg.decode()}")
    if msg == b'1':
        led.value(0)  # Active LOW LED ON
    else:
        led.value(1)  # LED OFF

# ------------------ MQTT Connection ------------------
def connect_mqtt():
    client = MQTTClient(CLIENT_ID, MQTT_SERVER, 1883)
    client.set_callback(mqtt_callback)
    client.connect()
    print("MQTT Connected")
    client.subscribe(TOPIC_SUB)
    print(f"Subscribed to {TOPIC_SUB.decode()}")
    return client

# ------------------ Main Logic ------------------
def main():
    connect_wifi()
    client = connect_mqtt()

    while True:
        client.check_msg()  # Check for incoming messages

        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        print(f"Temperature: {temp}°C")
        print(f"Humidity: {hum}%")

        client.publish(TOPIC_PUB_TEMP, str(temp))
        client.publish(TOPIC_PUB_HUM, str(hum))

        time.sleep(2)

# ------------------ Run Program ------------------
try:
    main()
except Exception as e:
    print("Error:", e)
    time.sleep(5)
    machine.reset()
