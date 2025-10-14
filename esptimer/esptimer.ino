#include <WiFi.h>
#include <PubSubClient.h>

// ===== WiFi Configuration =====
const char* ssid = "RADHE";
const char* password = "9173126511";

// ===== MQTT Configuration =====
const char* mqtt_server = "mqtt-dashboard.com";
const char* mqtt_user = "ansh2521";
const char* mqtt_pass = "anshansh";
const char* topic_sub = "/qos0";
const char* topic_pub = "/qos0";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
const long interval = 5000;  // 5 seconds
int counter = 100;

// ===== Function to Connect to WiFi =====
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// ===== Callback Function for Subscribed Topics =====
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");

  String msg;
  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.println(msg);

  // Example handling
  if (String(topic) == "notification" && msg == "received") {
    Serial.println("ESP received hello message");
  }
}

// ===== Reconnect Function =====
void reconnect() {
  // Loop until reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");

    // Attempt to connect with credentials
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      Serial.println("connected");

      // Subscribe to topic
      client.subscribe(topic_sub, 1);
      Serial.print("Subscribed to topic: ");
      Serial.println(topic_sub);

    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 10 seconds");
      delay(10000);
    }
  }
}

// ===== Setup =====
void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

// ===== Main Loop =====
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    String msg = "Only " + String(counter--) + " seconds left";
    Serial.print("Publishing message: ");
    Serial.println(msg);
    client.publish(topic_pub, msg.c_str(), true);  // QoS=0 equivalent behavior
  }
}
