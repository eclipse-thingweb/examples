import json
import time
import logging
from pymodbus.client import ModbusTcpClient

MODBUS_HOST = '192.168.20.76'
MODBUS_PORT = 502
UNIT_ID = 1
START_ADDRESS = 2
REGISTER_QUANTITY = 2
INCREMENT = 2 # sentron always has 2 registers per value
VALUE_QUANTITY = 6 # number of values to read

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logger")

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
            print (f"Read registers: {response.registers}")
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
                print (f"Read registers: {response.registers}")
            else:
                logger.error(f"Modbus Error: {response}")

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        mb_client.close()

if __name__ == "__main__":
    main()