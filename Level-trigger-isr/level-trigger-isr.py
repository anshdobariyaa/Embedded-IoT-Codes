import machine
import utime

# Pin setup
ir_sensor = machine.Pin(5, machine.Pin.IN)
led = machine.Pin(2, machine.Pin.OUT)

# Interrupt flag
object_detected = False

# ISR
def ir_handler(pin):
    global object_detected
    object_detected = True
    print("IR Sensor Detected Object (Level Triggered)")

# Attach interrupt for high level detection
# Note: ESP32 MicroPython may not support IRQ_HIGH_LEVEL directly.
# So we simulate it using RISING + polling logic.
ir_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=ir_handler)

# Main loop
while True:
    if object_detected:
        print("Toggling LED for 5 seconds...")
        start_time = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), start_time) < 5000:
            led.value(not led.value())
            utime.sleep(0.5)

            # If IR signal goes LOW → stop immediately
            if ir_sensor.value() == 0:
                print("IR signal lost, stopping toggle.")
                break

        led.value(0)
        object_detected = False
        print("LED OFF, waiting for next object...")

    utime.sleep(0.1)
