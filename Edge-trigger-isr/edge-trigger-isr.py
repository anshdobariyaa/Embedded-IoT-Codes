import machine
import utime

# Pin setup
button = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_DOWN)
led = machine.Pin(2, machine.Pin.OUT)

# Interrupt flag
button_pressed = False

# Interrupt Service Routine (ISR)
def button_handler(pin):
    global button_pressed
    button_pressed = True
    print("Button Press Detected (Edge Triggered)")

# Attach interrupt on rising edge
button.irq(trigger=machine.Pin.IRQ_RISING, handler=button_handler)

# Main loop
while True:
    if button_pressed:
        button_pressed = False
        print("Turning LED ON for 3 seconds...")
        led.value(1)
        utime.sleep(3)
        led.value(0)
        print("LED OFF, entering sleep mode.")
        
        # Simulate sleep mode
        utime.sleep(1)
