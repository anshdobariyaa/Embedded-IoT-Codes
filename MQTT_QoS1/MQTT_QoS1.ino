#include <WiFi.h>
#include <PubSubClient.h>

// ===== WiFi Configuration =====
const char* ssid = "RADHE";
const char* password = "9173126511";

// ===== MQTT Configuration =====
const char* mqtt_server = "mqtt-dashboard.com";
const char* mqtt_user = "ansh2521";
const char* mqtt_pass = "anshansh";
const char* topic_sub = "/qos1";
const char* topic_pub = "/qos1";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
const long interval = 5000;
int counter = 100;

void connectWiFi() {
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void onMessage(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on [");
  Serial.print(topic);
  Serial.print("]: ");
  for (int i = 0; i < length; i++) Serial.print((char)payload[i]);
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ESP32Client_QoS1", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      client.subscribe(topic_sub, 1);  // QoS 1
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(onMessage);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  if (millis() - lastMsg >= interval) {
    lastMsg = millis();
    String msg = "Only " + String(counter--) + " seconds left";
    Serial.print("Publishing (QoS1): ");
    Serial.println(msg);
    client.publish(topic_pub, msg.c_str(), true);  // QoS 1 ensures acknowledgment
  }
}
