import asyncio
import json
import logging
from wotpy.protocols.modbus.client import ModbusClient
from wotpy.wot.servient import Servient

TD_FILE = '../examples/sentron-pac.td.jsonld'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("logger")

async def main():
    with open(TD_FILE, 'r') as f:
        td_doc = json.load(f)

    servient = Servient(catalogue_port=None, clients=[ModbusClient()])
    wot = await servient.start()

    consumed_thing = wot.consume(json.dumps(td_doc))

    try:
        value = await consumed_thing.read_property('voltage-l1-n')
        logger.info(f"Read registers: {value}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await servient.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
