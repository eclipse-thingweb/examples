# Basics

Two scripts that read the `voltage-l1-n` property from a SENTRON PAC4200 over Modbus TCP — one using pymodbus directly, one using WoTPy with the device's Thing Description.

## Setup

```bash
pip install -r requirements.txt
```

## Run

Raw pymodbus (hardcoded address/registers):
```bash
python read-modbus-sentron.py
```

WoTPy with Thing Description (address comes from the TD):
```bash
python read-modbus-sentron-wot.py
```

The TD file is at `../examples/sentron-pac.td.jsonld`. Update the `base` URL in it to match your device's IP address.
