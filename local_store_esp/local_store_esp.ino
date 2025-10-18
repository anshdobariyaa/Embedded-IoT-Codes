#include <WiFi.h>
#include <PubSubClient.h>
#include <Preferences.h>

Preferences prefs;

const char* ssid = "iPhone";
const char* password = "jeeljeel";

const char* mqtt_server = "mqtt-dashboard.com";
const char* mqtt_user = "ansh";
const char* mqtt_pass = "ansh";
const char* topic_pub = "/local";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
unsigned long lastReconnectAttempt = 0;
int counter = 100;
bool countingDown = true;

//----------------- Wi-Fi Setup -----------------
void setup_wifi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

//----------------- MQTT Reconnect -----------------
bool reconnect() {
  Serial.print("Connecting to MQTT...");
  if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
    Serial.println("Connected to MQTT");
    sendStoredData(); // send any locally stored data
    return true;
  } else {
    Serial.print("Failed, rc=");
    Serial.println(client.state());
    return false;
  }
}

//----------------- Store Data -----------------
void storeDataLocally(int value) {
  prefs.begin("localdata", false);
  int index = prefs.getInt("index", 0);       // read last index
  String key = "val" + String(index);         // key = val0, val1, ...
  prefs.putInt(key.c_str(), value);           // store value
  prefs.putInt("index", index + 1);           // increment index
  prefs.end();
  Serial.printf("Stored locally [%s] = %d\n", key.c_str(), value);
}

//----------------- Send Stored Data -----------------
void sendStoredData() {
  prefs.begin("localdata", false);
  int index = prefs.getInt("index", 0);

  if (index > 0) {
    Serial.println("Sending stored data to MQTT...");
    for (int i = 0; i < index; i++) {
      String key = "val" + String(i);
      int val = prefs.getInt(key.c_str(), -1);
      if (val != -1) {
        String msg = "Recovered data: " + String(val);
        if (client.publish(topic_pub, msg.c_str())) {
          Serial.printf("Sent stored [%s] = %d\n", key.c_str(), val);
        } else {
          Serial.println("MQTT publish failed, will retry later");
          prefs.end();
          return;
        }
      }
    }
    prefs.clear(); // all sent successfully → clear memory
    Serial.println("Local storage cleared after sending.");
  }
  prefs.end();
}

//----------------- Counter Logic -----------------
int getNextCounterValue() {
  int value = counter;
  if (countingDown) {
    counter--;
    if (counter <= 0) countingDown = false;
  } else {
    counter++;
    if (counter >= 100) countingDown = true;
  }
  return value;
}

//----------------- Setup -----------------
void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  prefs.begin("localdata", false);
  prefs.putInt("index", prefs.getInt("index", 0)); // ensure key exists
  prefs.end();
}

//----------------- Loop -----------------
void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    unsigned long now = millis();
    if (now - lastReconnectAttempt > 5000) {  // retry every 5 seconds
      lastReconnectAttempt = now;
      reconnect();
    }
  } else {
    client.loop();
  }

  // Publish every 5 seconds
  unsigned long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;

    int value = getNextCounterValue();
    String msg = "Counter Value: " + String(value);

    if (client.connected()) {
      bool success = client.publish(topic_pub, msg.c_str());
      if (success) {
        Serial.printf("Sent to MQTT: %d\n", value);
      } else {
        Serial.println("MQTT publish failed, storing locally...");
        storeDataLocally(value);
      }
    } else {
      storeDataLocally(value);
    }
  }
}
