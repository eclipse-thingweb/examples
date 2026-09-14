#!/bin/sh
set -eu

/zenoh-bridge-mqtt "$@" &
bridge_pid=$!

cleanup() {
    kill "$bridge_pid" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

python3 /usr/local/bin/mqtt_demux.py &
demux_pid=$!

wait "$bridge_pid"