import network
import socket
import time
import os
import ure as re
import machine
try:
    import esp
except:
    esp = None

# ----------------------
# = User configuration =
# ----------------------
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASS = ""

# File where uploaded firmware is saved
UPDATE_FILENAME = "/update.bin"

# HTML upload page 
UPLOAD_PAGE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>OTA Upload</title>
<style>
#barContainer{width:100%;height:20px;background:#ddd;border-radius:5px;margin-top:10px;}
#progressBar{width:0%;height:100%;background:#4CAF50;border-radius:5px;}
#statusMsg{margin-top:10px;font-weight:bold;}
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
</head>
<body>
<form method='POST' action='/update' enctype='multipart/form-data' id='upload_form'>
<input type='file' name='update'>
<input type='submit' value='Upload Firmware'>
</form>
<div id='barContainer'><div id='progressBar'></div></div>
<div id='statusMsg'></div>
<script>
$('form').submit(function(e){
  e.preventDefault();
  $('#statusMsg').html('Uploading...');
  var data = new FormData($('#upload_form')[0]);
  $.ajax({
    url: '/update', type: 'POST', data: data, contentType: false, processData:false,
    xhr: function() {
      var xhr = new window.XMLHttpRequest();
      xhr.upload.addEventListener('progress', function(evt) {
        if (evt.lengthComputable) {
          $('#progressBar').css('width', Math.round((evt.loaded / evt.total) * 100) + '%');
        }
      }, false);
      return xhr;
    },
    success:function() { $('#statusMsg').html('Code Uploaded Successfully! Rebooting...'); },
    error: function() { $('#statusMsg').html('Upload Failed!'); }
  });
});
</script>
</body>
</html>
"""

# -------------------------
# = WiFi connect function =
# -------------------------
def connect_wifi(ssid, password, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi '{}'...".format(ssid))
        wlan.connect(ssid, password)
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                raise RuntimeError("Failed to connect to WiFi within timeout")
            time.sleep(0.5)
    print("WiFi connected, IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

# -------------------------
# = Minimal HTTP server   =
# -------------------------
# Note: MicroPython's socket HTTP server is used. We implement
# simple handlers for GET / and POST /update with multipart parsing.

CRLF = b"\r\n"

def start_server(ip, port=80):
    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Listening on http://{}:{}".format(ip, port))

    while True:
        cl, addr = s.accept()
        cl_file = cl.makefile('rwb', 0)
        try:
            request_line = cl_file.readline()
            if not request_line:
                cl.close()
                continue
            request_line = request_line.decode()
            method, path, proto = request_line.split()
            # Read headers
            headers = {}
            while True:
                line = cl_file.readline()
                if not line or line == b'\r\n':
                    break
                hline = line.decode().strip()
                if ':' in hline:
                    k, v = hline.split(':', 1)
                    headers[k.strip().lower()] = v.strip()
            # Handle GET /
            if method == 'GET' and path == '/':
                send_response(cl, 200, "text/html", UPLOAD_PAGE.encode())
            # Handle POST /update
            elif method == 'POST' and path.startswith('/update'):
                content_type = headers.get('content-type', '')
                # Expect multipart/form-data; boundary=---
                m = re.search(r'boundary=(.*)', content_type)
                if not m:
                    send_response(cl, 400, "text/plain", b"No boundary in Content-Type")
                else:
                    boundary = m.group(1)
                    # boundary comes in as string like -------------------xyz
                    # read raw body from socket and parse multipart streaming to file
                    try:
                        length = int(headers.get('content-length', '0'))
                    except:
                        length = 0
                    if length == 0:
                        send_response(cl, 400, "text/plain", b"No content length")
                    else:
                        # Read exactly `length` bytes from cl_file
                        remaining = length
                        # We'll parse multipart by searching for CRLF + boundary markers.
                        # Simpler approach: read all body into memory (careful on large files).
                        # For safety, attempt streaming read and write to file.
                        body = cl_file.read(remaining)
                        # Now parse body to extract the file content for form field 'update'
                        # Look for first double CRLF after headers for the part, then find final boundary
                        boundary_bytes = ("--" + boundary).encode()
                        parts = body.split(boundary_bytes)
                        found = False
                        for part in parts:
                            if b'Content-Disposition' in part and b'name="update"' in part:
                                # strip leading CRLF
                                p = part
                                # find blank line after part headers
                                idx = p.find(b'\r\n\r\n')
                                if idx != -1:
                                    filedata = p[idx+4:]
                                    # trim trailing CRLF and '--' if present
                                    if filedata.endswith(b'\r\n'):
                                        filedata = filedata[:-2]
                                    # Also remove trailing '--' markers if present at end
                                    filedata = filedata.rstrip(b'\r\n-')
                                    # save to disk
                                    try:
                                        with open(UPDATE_FILENAME, "wb") as f:
                                            f.write(filedata)
                                        print("Saved uploaded file to", UPDATE_FILENAME)
                                        found = True
                                    except Exception as e:
                                        print("Error saving file:", e)
                                break
                        if not found:
                            # Fallback: if multipart parse failed, try to find binary by heuristics
                            try:
                                with open(UPDATE_FILENAME, "wb") as f:
                                    f.write(body)
                                found = True
                                print("Saved raw body to", UPDATE_FILENAME)
                            except Exception as e:
                                print("Fallback save failed:", e)
                        if found:
                            # Respond OK then restart
                            send_response(cl, 200, "text/plain", b"OK")
                            cl.close()
                            print("Rebooting in 2s...")
                            time.sleep(2)
                            machine.reset()
                            return
                        else:
                            send_response(cl, 500, "text/plain", b"Failed to extract upload")
            else:
                send_response(cl, 404, "text/plain", b"Not found")
        except Exception as ex:
            print("Server error:", ex)
            try:
                send_response(cl, 500, "text/plain", b"Server Error")
            except:
                pass
        finally:
            try:
                cl.close()
            except:
                pass

def send_response(cl, status_code, content_type, content):
    reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Server Error"}.get(status_code, "OK")
    cl.send("HTTP/1.1 {} {}\r\n".format(status_code, reason))
    cl.send("Content-Type: {}\r\n".format(content_type))
    cl.send("Content-Length: {}\r\n".format(len(content)))
    cl.send("Connection: close\r\n")
    cl.send("\r\n")
    if isinstance(content, str):
        content = content.encode()
    cl.send(content)


def flash_bin_to_address(bin_path, flash_offset):
    if esp is None:
        raise RuntimeError("esp module is not available on this build")
    # Read file
    with open(bin_path, "rb") as f:
        data = f.read()
    # Erase needed sectors (sector size 0x1000)
    sec_size = 0x1000
    total = len(data)
    nsec = (total + sec_size - 1) // sec_size
    print("Erasing {} sectors starting at offset 0x{:x}".format(nsec, flash_offset))
    for i in range(nsec):
        esp.flash_erase((flash_offset // sec_size) + i)
    print("Writing {} bytes".format(total))
    # esp.flash_write expects 4-byte aligned writes; write in chunks
    pos = 0
    while pos < total:
        chunk = data[pos:pos+4096]
        esp.flash_write(flash_offset + pos, chunk)
        pos += len(chunk)
    print("Flash write complete. Resetting.")
    machine.reset()


# ----------------------
# = Run main program   =
# ----------------------
def main():
    try:
        ip = connect_wifi(WIFI_SSID, WIFI_PASS)
    except Exception as e:
        print("WiFi error:", e)
        ip = "0.0.0.0"
    # Print info every few seconds in separate thread would be nicer but we keep main simple
    start_server(ip, port=80)

if __name__ == "__main__":
    main()

