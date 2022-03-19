
## Example docker-compose.yml file:
```
prometheus-dyson-exporter:
    image: zkhcohen/prometheus-dyson-exporter:latest
    container_name: prometheus-dyson-exporter
    ports:
      - "9672:9672"
    volumes:
      - /devices.ini:/config/devices.ini
    environment:
      EXPORTER_PORT="9672"
      EXPORTER_LOG_LEVEL="INFO"
      CONFIG_PATH="/config/devices.ini"
    restart: always
```

## Example devices.ini config file:
```
[My Dyson Air Purifier]
dyson_serial = F4P-US-PT338B
dyson_credential = ajds3AS+FPsidcQ8VxNmfJXHqFFNoBLaCaWRQTeTMnwVPhsH6rocz8UJ2puatCpszzvaQwYYL3mnsCqEgAGgc9X==
dyson_device_type = 438
dyson_ip = 10.0.10.2
```
