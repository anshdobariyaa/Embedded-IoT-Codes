#include <WiFi.h>
#include <WebServer.h>
#include <Update.h>

const char* wifiSSID = "RADHE";
const char* wifiPASS = "9173126511";

WebServer otaServer(80);

// HTML OTA Page
const char* uploadPage = 
"<style>"
"#barContainer{width:100%;height:20px;background:#ddd;border-radius:5px;margin-top:10px;}"
"#progressBar{width:0%;height:100%;background:#4CAF50;border-radius:5px;}"
"#statusMsg{margin-top:10px;font-weight:bold;}"
"</style>"
"<script src='https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js'></script>"
"<form method='POST' action='#' enctype='multipart/form-data' id='upload_form'>"
"<input type='file' name='update'>"
"<input type='submit' value='Upload Firmware'>"
"</form>"
"<div id='barContainer'><div id='progressBar'></div></div>"
"<div id='statusMsg'></div>"
"<script>"
"$('form').submit(function(e){"
"e.preventDefault();"
"$('#statusMsg').html('Uploading...');"
"var data = new FormData($('#upload_form')[0]);"
"$.ajax({"
"url: '/update', type: 'POST', data: data, contentType: false, processData:false,"
"xhr: function() {"
"var xhr = new window.XMLHttpRequest();"
"xhr.upload.addEventListener('progress', function(evt) {"
"if (evt.lengthComputable) {"
"$('#progressBar').css('width', Math.round((evt.loaded / evt.total) * 100) + '%');"
"}"
"}, false); return xhr; },"
"success:function() { $('#statusMsg').html('Code Uploaded Successfully! Rebooting...'); },"
"error: function() { $('#statusMsg').html('Upload Failed!'); }"
"});"
"});"
"</script>";

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(wifiSSID, wifiPASS);
  Serial.println("\nConnecting to WiFi...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  delay(1000);

  // Connection Info
  Serial.println("\nWiFi Connected!");
  Serial.print("Network: ");
  Serial.println(wifiSSID);
  Serial.print("Device IP: ");
  Serial.println(WiFi.localIP());

  otaServer.on("/", HTTP_GET, []() {
    otaServer.send(200, "text/html", uploadPage);
  });

  otaServer.on("/update", HTTP_POST, []() {
    otaServer.send(200, "text/plain", (Update.hasError()) ? "FAIL" : "OK");
    ESP.restart();
  }, []() {
    HTTPUpload& firmware = otaServer.upload();
    if (firmware.status == UPLOAD_FILE_START) {
      Update.begin(UPDATE_SIZE_UNKNOWN);
    } else if (firmware.status == UPLOAD_FILE_WRITE) {
      Update.write(firmware.buf, firmware.currentSize);
    } else if (firmware.status == UPLOAD_FILE_END) {
      Update.end(true);
    }
  });

  otaServer.begin();
}

void loop() {
  otaServer.handleClient();
  Serial.println("You Can Upload code using IP");
  delay(1000);
}
