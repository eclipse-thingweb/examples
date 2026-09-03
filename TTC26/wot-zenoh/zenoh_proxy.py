#!/usr/bin/env python

"""
Usage:
    python zenoh_proxy.py --source-td ./thing-td.json [--source-binding modbus] \
        [--router tcp/localhost:7447]
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from urllib.parse import urlparse

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXAMPLE_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLE_DIR)

from tornado.ioloop import IOLoop

from wotpy.protocols.modbus.client import ModbusClient
from wotpy.protocols.zenoh.server import ZenohServer
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

_RUNNING_SERVIENT = None

TIMEOUT_PROP_READ = 30.0
TIMEOUT_PROP_WRITE = 30.0
TIMEOUT_HARD_FACTOR = 1.2
EVENT_RESUBSCRIBE_DELAY = 2.0
EVENT_RESUBSCRIBE_MAX_DELAY = 60.0


def _strip_binding_terms(interaction):
    clean = {
        key: value for key, value in interaction.items()
        if key != "forms" and not key.startswith(("modv:", "modbus:", "mqtt:"))
    }

    clean.setdefault("observable", True)

    return clean


def build_property_read_proxy(consumed_thing, name):
    async def _proxy():
        awaitable = consumed_thing.properties[name].read(timeout=TIMEOUT_PROP_READ)
        return await asyncio.wait_for(awaitable, timeout=TIMEOUT_PROP_READ * TIMEOUT_HARD_FACTOR)

    return _proxy


def build_property_write_proxy(consumed_thing, name):
    async def _proxy(value):
        awaitable = consumed_thing.properties[name].write(value, timeout=TIMEOUT_PROP_WRITE)
        await asyncio.wait_for(awaitable, timeout=TIMEOUT_PROP_WRITE * TIMEOUT_HARD_FACTOR)

    return _proxy


def subscribe_event_proxy(consumed_thing, exposed_thing, name):
    state = {"subscription": None, "delay": EVENT_RESUBSCRIBE_DELAY}

    def subscribe():
        state["subscription"] = consumed_thing.events[name].subscribe(
            on_next=on_next,
            on_error=on_error)

    def on_next(item):
        state["delay"] = EVENT_RESUBSCRIBE_DELAY
        exposed_thing.events[name].emit(item.data)

    def on_error(error):
        delay = state["delay"]
        LOGGER.warning("Source event '%s' failed: %s (retrying in %.0fs)", name, error, delay)
        subscription = state["subscription"]
        if subscription is not None:
            subscription.dispose()
        asyncio.get_event_loop().call_later(delay, subscribe)
        state["delay"] = min(delay * 2, EVENT_RESUBSCRIBE_MAX_DELAY)

    subscribe()


def build_proxy_td(source_td, thing_id, thing_title, property_names):
    source_properties = source_td.get("properties", {})
    source_events = source_td.get("events", {})

    return {
        "@context": [
            "https://www.w3.org/2019/wot/td/v1",
            "https://www.w3.org/2022/wot/td/v1.1",
        ],
        "id": thing_id,
        "title": thing_title,
        "description": "Zenoh proxy for the source Thing '{}'".format(source_td.get("title", "")),
        "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
        "security": "nosec_sc",
        "properties": {
            name: _strip_binding_terms(source_properties[name]) for name in property_names
        },
        "events": {
            name: _strip_binding_terms(source_events[name]) for name in source_events
        },
    }


def preview_proxy_td(source_td, thing_id, thing_title, max_properties, router_url):
    property_names = list(source_td.get("properties", {}).keys())[:max_properties]
    proxy_td = build_proxy_td(source_td, thing_id, thing_title, property_names)

    thing = Thing(thing_fragment=ThingDescription(proxy_td).to_thing_fragment())
    zenoh_server = ZenohServer(router_url=router_url)

    for interaction in thing.properties.values():
        for form in zenoh_server.build_forms(hostname=None, interaction=interaction):
            interaction.add_form(form)

    for interaction in thing.events.values():
        for form in zenoh_server.build_forms(hostname=None, interaction=interaction):
            interaction.add_form(form)

    return ThingDescription.from_thing(thing).to_dict()


async def expose_proxy(wot, consumed_thing, source_td, thing_id, thing_title, max_properties):
    property_names = list(consumed_thing.td.properties.keys())[:max_properties]
    proxy_td = build_proxy_td(source_td, thing_id, thing_title, property_names)

    exposed_thing = wot.produce(json.dumps(proxy_td))

    for name in property_names:
        exposed_thing.set_property_read_handler(name, build_property_read_proxy(consumed_thing, name))
        exposed_thing.set_property_write_handler(name, build_property_write_proxy(consumed_thing, name))

    for name in consumed_thing.td.events:
        subscribe_event_proxy(consumed_thing, exposed_thing, name)

    exposed_thing.expose()

    return exposed_thing


def infer_source_binding(source_td):
    schemes = [urlparse(str(source_td.get("base", ""))).scheme]

    for interaction_map in (source_td.get("properties", {}), source_td.get("events", {})):
        for interaction in interaction_map.values():
            for form in interaction.get("forms", []):
                schemes.append(urlparse(str(form.get("href", ""))).scheme)

    for scheme in schemes:
        if scheme.startswith("modbus"):
            return "modbus"
        if scheme.startswith("mqtt"):
            return "mqtt"

    raise ValueError("Could not infer a source binding; pass --source-binding explicitly")


def build_source_client(source_binding):
    if source_binding == "modbus":
        return ModbusClient()

    if source_binding == "mqtt":
        from wotpy.protocols.mqtt.client import MQTTClient
        return MQTTClient()

    raise ValueError("Unsupported source binding: {}".format(source_binding))


def _slugify_urn(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _load_source(source_td_path, source_binding):
    with open(source_td_path, "r", encoding="utf-8") as fobj:
        source_td = json.load(fobj)

    source_binding = infer_source_binding(source_td) if source_binding == "auto" else source_binding

    return source_td, source_binding


def _proxy_identity(source_td, thing_id, thing_title, is_only_source):
    if is_only_source:
        return thing_id, thing_title

    slug = _slugify_urn(source_td.get("title", "thing"))
    return "urn:zenoh:proxy:{}".format(slug), source_td.get("title", "ZenohProxy")


async def main(source_td_paths, source_bindings, router_url, max_properties, thing_id, thing_title, catalogue_port, servient_id=None, dry_run=False):
    source_bindings = list(source_bindings) + ["auto"] * (len(source_td_paths) - len(source_bindings))
    sources = [_load_source(path, binding) for path, binding in zip(source_td_paths, source_bindings)]
    is_only_source = len(sources) == 1

    if dry_run:
        previews = [
            preview_proxy_td(
                source_td,
                *_proxy_identity(source_td, thing_id, thing_title, is_only_source),
                max_properties,
                router_url)
            for source_td, _ in sources
        ]
        print(json.dumps(previews if len(previews) > 1 else previews[0], indent=2))
        IOLoop.current().stop()
        return

    bindings_needed = {binding for _, binding in sources}
    clients = {binding: build_source_client(binding) for binding in bindings_needed}

    servient = Servient(catalogue_port=catalogue_port, clients=list(clients.values()))
    servient.add_server(ZenohServer(router_url=router_url, servient_id=servient_id))

    global _RUNNING_SERVIENT
    _RUNNING_SERVIENT = servient

    wot = await servient.start()

    for source_td, source_binding in sources:
        LOGGER.info("Consuming source Thing using the %s binding", source_binding)

        consumed_thing = wot.consume(json.dumps(source_td))
        proxy_thing_id, proxy_thing_title = _proxy_identity(source_td, thing_id, thing_title, is_only_source)

        exposed_thing = await expose_proxy(
            wot=wot,
            consumed_thing=consumed_thing,
            source_td=source_td,
            thing_id=proxy_thing_id,
            thing_title=proxy_thing_title,
            max_properties=max_properties)

        exposed_td = ThingDescription.from_thing(exposed_thing.thing).to_dict()
        print(json.dumps(exposed_td, indent=2))

    LOGGER.info("Zenoh proxy for %d source(s) exposed on router %s", len(sources), router_url)

    if catalogue_port is not None:
        LOGGER.info("TD catalogue available at http://localhost:%s", catalogue_port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expose one or more source Things as Zenoh proxy Things")
    parser.add_argument("--source-td", action="append", required=True, help="Path to a valid source Thing Description (repeatable)")
    parser.add_argument("--source-binding", action="append", choices=["auto", "modbus", "mqtt"], default=[], help="Source protocol binding per --source-td, same order (default: infer from TD forms)")
    parser.add_argument("--router", default="tcp/localhost:7447", help="Zenoh router URL")
    parser.add_argument("--max-properties", type=int, default=15, help="Maximum number of properties to proxy")
    parser.add_argument("--thing-id", default="urn:modbus:zenoh:proxy", help="ID of the exposed Zenoh Thing (only used with a single --source-td)")
    parser.add_argument("--thing-title", default="ModbusZenohProxy", help="Title of the exposed Zenoh Thing (only used with a single --source-td)")
    parser.add_argument("--catalogue-port", type=int, default=9292, help="TD catalogue port (0 to disable)")
    parser.add_argument("--servient-id", default=None, help="Zenoh servient/topic namespace (default: 'wotpy'). Set this to avoid colliding with other proxy instances sharing the same router.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the proxy TD(s); do not connect to any source or Zenoh")
    args = parser.parse_args()

    IOLoop.current().add_callback(
        main,
        source_td_paths=args.source_td,
        source_bindings=args.source_binding,
        router_url=args.router,
        max_properties=args.max_properties,
        thing_id=args.thing_id,
        thing_title=args.thing_title,
        catalogue_port=args.catalogue_port or None,
        servient_id=args.servient_id,
        dry_run=args.dry_run)

    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        LOGGER.info("Interrupted, closing the Zenoh session...")
        if _RUNNING_SERVIENT is not None:
            IOLoop.current().run_sync(_RUNNING_SERVIENT.shutdown)
