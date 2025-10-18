#include <WiFi.h>
#include <WiFiClient.h>

// WiFi credentials
const char* ssid = "RADHE";
const char* password = "9173126511";

// Modbus server
const char* serverIP = "192.168.29.92";
const uint16_t serverPort = 502;

WiFiClient client;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());
}

void testModbusRaw() {
  if (!client.connect(serverIP, serverPort)) {
    Serial.println("Connection failed!");
    return;
  }
  
  Serial.println("Connected to Modbus server");
  
  // Raw Modbus TCP frame to read 5 holding registers at address 0
  uint8_t request[] = {
    0x00, 0x01,  // Transaction ID
    0x00, 0x00,  // Protocol ID (always 0)
    0x00, 0x06,  // Length (6 bytes follow)
    0x01,        // Unit ID
    0x03,        // Function code (Read Holding Registers)
    0x00, 0x00,  // Start address (0)
    0x00, 0x05   // Quantity (5 registers)
  };
  
  // Send request
  client.write(request, sizeof(request));
  client.flush();
  
  Serial.print("Sent request: ");
  for (int i = 0; i < sizeof(request); i++) {
    Serial.printf("%02X ", request[i]);
  }
  Serial.println();
  
  // Wait for response
  delay(500);
  
  if (client.available()) {
    uint8_t response[256];
    int len = client.readBytes(response, client.available());
    
    Serial.printf("Received %d bytes: ", len);
    for (int i = 0; i < len; i++) {
      Serial.printf("%02X ", response[i]);
    }
    Serial.println();
    
    // Parse response if valid
    if (len >= 9 && response[7] == 0x03) {
      int dataBytes = response[8];
      Serial.printf("Data bytes: %d\n", dataBytes);
      
      for (int i = 0; i < dataBytes/2; i++) {
        uint16_t value = (response[9 + i*2] << 8) | response[10 + i*2];
        Serial.printf("Register %d: %d\n", i, (int)value);
      }
    } else {
      Serial.println("Invalid or error response");
    }
  } else {
    Serial.println("No response received");
  }
  
  client.stop();
}

void loop() {
  Serial.println("\n=== Testing Modbus Connection ===");
  testModbusRaw();
  delay(5000);
}
