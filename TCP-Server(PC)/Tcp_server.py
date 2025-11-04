from pymodbus.version import version
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
import threading
from time import sleep
from random import randint

def update_registers(context):
    """Continuously update holding registers with random values"""
    counter = 1
    while True:
        try:
            # Generate random values
            values = [randint(10, 99) for _ in range(5)]
            
            # Update holding registers (function code 3, address 0)
            slaves = context[0]  # Get slave ID 0
            slaves.setValues(3, 0, values)  # 3 = holding registers
            
            # Verify values were set
            current_values = slaves.getValues(3, 0, 5)
            
            print(f"Updated holding registers: {values}")
            print(f"Verified values: {current_values}")
            print("-" * 50)
            
            counter += 1
            sleep(3)
            
        except Exception as e:
            print(f"Error updating registers: {e}")
            sleep(1)

# Initialize data blocks with starting values
print("Initializing Modbus data blocks...")
holding_registers = ModbusSequentialDataBlock(0, [10, 20, 30, 40, 50])
input_registers = ModbusSequentialDataBlock(0, [0]*100)
coils = ModbusSequentialDataBlock(0, [0]*100)
discrete_inputs = ModbusSequentialDataBlock(0, [0]*100)

# Create slave context
slave_context = ModbusSlaveContext(
    di=discrete_inputs,      # Discrete Inputs
    co=coils,                # Coils
    hr=holding_registers,    # Holding Registers
    ir=input_registers,      # Input Registers
    zero_mode=True           # Use 0-based addressing
)

# Create server context
server_context = ModbusServerContext(slaves=slave_context, single=True)

# Optional: Device identification
identity = ModbusDeviceIdentification()
identity.VendorName = 'ESP32-Modbus'
identity.ProductCode = 'PM'
identity.VendorUrl = 'http://localhost/'
identity.ProductName = 'Modbus TCP Server'
identity.ModelName = 'Modbus Server'
identity.MajorMinorRevision = version.short()

print("Starting Modbus TCP Server on 0.0.0.0:502...")
print("Press Ctrl+C to stop")

# Start background thread to update registers
update_thread = threading.Thread(target=update_registers, args=(server_context,), daemon=True)
update_thread.start()

# Start the server (blocking call)
try:
    StartTcpServer(
        context=server_context,
        identity=identity,
        address=("0.0.0.0", 502),
        allow_reuse_address=True
    )
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Server error: {e}")
