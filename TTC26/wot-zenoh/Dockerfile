FROM eclipse/zenoh-bridge-mqtt:latest

RUN mkdir -p /etc/zenoh

RUN apk add --no-cache python3 py3-pip \
	&& python3 -m pip install --no-cache-dir --break-system-packages paho-mqtt

COPY config.json5 /etc/zenoh/config.json5
COPY mqtt_demux.py /usr/local/bin/mqtt_demux.py
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8883

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

CMD ["-c", "/etc/zenoh/config.json5"]