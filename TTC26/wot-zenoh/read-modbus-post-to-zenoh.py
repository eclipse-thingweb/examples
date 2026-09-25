import zenoh
import json
import time
import logging
import struct
from pymodbus.client import ModbusTcpClient

MODBUS_HOST = '192.168.100.110'
MODBUS_PORT = 502
UNIT_ID = 1
START_ADDRESS = 1
QUANTITY = 2
ZENOH_KEY = 'test/modbus'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logger")

def to_float32(registers):
    return struct.unpack('>f', struct.pack('>HH', *registers))[0]

def main():
    logger.info("Opening Zenoh session...")
    conf = zenoh.Config()
    conf.insert_json5("listen/endpoints", '["tcp/localhost:7447"]')
    
    z_session = zenoh.open(conf)

    logger.info(f"Connecting to Modbus TCP at {MODBUS_HOST}:{MODBUS_PORT}...")
    mb_client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

    try:
        while True:
            if not mb_client.connected:
                mb_client.connect()

            response = mb_client.read_holding_registers(
                address=START_ADDRESS, 
                count=QUANTITY, 
                device_id=UNIT_ID
            )

            if not response.isError():
                parsed = to_float32(response.registers)
                data = {
                    "timestamp": time.time(),
                    "values": parsed
                }
                z_session.put(ZENOH_KEY, json.dumps(data))
                logger.info(f"Published: {parsed}")
            else:
                logger.error(f"Modbus Error: {response}")

            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        mb_client.close()
        z_session.close()

if __name__ == "__main__":
    main()