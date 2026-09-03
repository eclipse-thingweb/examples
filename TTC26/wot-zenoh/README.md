
# Zenoh-Modbus Demo

1.  Start the zenoh router:
    ```bash
    docker-compose up -d
    ```

The proxy script acts as a bridge. It consumes the local Modbus device's Thing Description (TD), creates a new northbound Zenoh-compatible TD, and handles the real-time translation of data.

2.  Ensure you have a running Modbus device (or simulator) and its corresponding `thing-td.json`.
3.  Run the proxy script (requires ModbusClient from https://github.com/ki-do/wotpy/tree/ttc/wotpy/protocols/modbus):
    ```bash
    python3 zenoh_proxy.py --source-td thing-td.json --router tcp/localhost:7447
    ```
	You will see the generated Northbound TD printed in your terminal.

Once the proxy is active, the Modbus data is available on the Zenoh network. You can verify this by querying the Zenoh router directly using the CLI tools.

4.  Run the `z_get` command:
    ```bash
    z_get -e tcp/localhost:7447 -s "wotpy/property/requests/modbuszenohproxy/integer-property"
    ```

5.  Expected Output:
    If the proxy is successfully communicating with the Modbus device, you will receive the current value and a timestamp:
    ```text
    Opening session...
    Sending Query 'wotpy/property/requests/modbuszenohproxy/integer-property'...
    >> Received ('wotpy/property/requests/modbuszenohproxy/integer-property': '{"value": [1, 2, 3, 4], "timestamp": 1788442424016}')
    ```
	
## Dashboard

the dashboard sitting on top of zenoh can be started by simply running:

```bash
python3 dashboard.py
```