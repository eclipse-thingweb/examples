import asyncio
import json
import struct
import logging
from wotpy.protocols.modbus.client import ModbusClient
from wotpy.wot.servient import Servient

TD_FILE = '../examples/sentron-pac.td.jsonld'
PROPERTIES = [
    'voltage-l1-n',
    'voltage-l2-n',
    'voltage-l3-n',
    'voltage-l1-l2',
    'voltage-l2-l3',
    'voltage-l3-l1',
]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logger")

def to_float32(registers):
    return struct.unpack('>f', struct.pack('>HH', *registers))[0]

async def main():
    with open(TD_FILE, 'r') as f:
        td_doc = json.load(f)

    servient = Servient(catalogue_port=None, clients=[ModbusClient()])
    wot = await servient.start()

    consumed_thing = wot.consume(json.dumps(td_doc))

    try:
        for name in PROPERTIES:
            try:
                value = await consumed_thing.read_property(name)
                print(f"{name}: {to_float32(value)}")
            except Exception as e:
                logger.error(f"Error reading {name}: {e}")
            await asyncio.sleep(1)
    finally:
        await servient.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
