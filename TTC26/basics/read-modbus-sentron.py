import json
import time
import struct
import logging
from pymodbus.client import ModbusTcpClient

MODBUS_HOST = '192.168.100.110'
MODBUS_PORT = 502
UNIT_ID = 1
START_ADDRESS = 1 # sentron measured values block starts at offset 1
REGISTER_QUANTITY = 2
INCREMENT = 2 # sentron always has 2 registers per value
VALUE_QUANTITY = 6 # number of values to read

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logger")

def to_float32(registers):
    return struct.unpack('>f', struct.pack('>HH', *registers))[0]

def main():
    logger.info(f"Connecting to Modbus TCP at {MODBUS_HOST}:{MODBUS_PORT}...")
    mb_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

    try:
        if not mb_client.connected:
            mb_client.connect()

        response = mb_client.read_holding_registers(
            address=START_ADDRESS, 
            count=REGISTER_QUANTITY, 
            device_id=UNIT_ID
        )

        if not response.isError():
            print (f"Value: {to_float32(response.registers)}")
        else:
            logger.error(f"Modbus Error: {response}")

        time.sleep(1)

        for i in range(1, VALUE_QUANTITY):
            response = mb_client.read_holding_registers(
                address=START_ADDRESS + (i * INCREMENT), 
                count=REGISTER_QUANTITY, 
                device_id=UNIT_ID
            )

            if not response.isError():
                print (f"Value: {to_float32(response.registers)}")
            else:
                logger.error(f"Modbus Error: {response}")

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        mb_client.close()

if __name__ == "__main__":
    main()