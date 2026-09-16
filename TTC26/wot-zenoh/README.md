
# Zenoh-Modbus Demo

1. Build wotpy with modbus support from the root of https://github.com/ki-do/wotpy/tree/ttc:
    ```bash
    docker build -t wotpy-modbus:latest .
    ```

2.  Start the compose, incl. zenoh-router, zenoh-mqtt-bridge, wotpy modbus proxy and the dashboard:
    ```bash
    docker-compose up -d
    ```

The proxy script acts as a bridge. It consumes the local Modbus device's Thing Description (TD), creates a new northbound Zenoh-compatible TD, and handles the real-time translation of data. For LoRaWan devices, it creates the NB TD that consumes the messages, chirpstack is publishing at zenoh-mqtt-bridge.

3. Dashborad is running at localhost:8899 