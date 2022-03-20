import time
import os
from os import path
import sys
import signal
import faulthandler
import configparser as c
import logging
import libdyson as ld
from libdyson.exceptions import DysonException
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from pythonjsonlogger import jsonlogger

# Enable dumps on stderr in case of segfault
faulthandler.enable()
logger = logging.getLogger()

class DysonMetricsCollector():

    def __init__(self, config_path, dyson_serial, dyson_credential, dyson_device_type, dyson_ip):
        self.config_path = config_path
        self.dyson_serial = dyson_serial
        self.dyson_credential = dyson_credential
        self.dyson_device_type = dyson_device_type
        self.dyson_ip = dyson_ip

    def collect(self):
        logger.info("Fetching metrics")
        metrics = self.get_metrics()

        for metric in metrics or []:
            name = metric["name"]
            value = metric["value"]

            metric = GaugeMetricFamily(name, name)
            metric.add_metric(value=value, labels=name)
            yield metric

    def get_metrics(self):
        metrics = []
        dyson_devices = c.ConfigParser()

        if path.exists(self.config_path) and path.isfile(self.config_path):

            dyson_devices.read(self.config_path)

            # TODO: Make this compile statistics for multiple devices.
            for section in dyson_devices.sections():
                try:
                    device = ld.get_device(
                        dyson_devices[section]["dyson_serial"],
                        dyson_devices[section]["dyson_credential"],
                        dyson_devices[section]["dyson_device_type"]
                    )

                
                    device.connect(dyson_devices[section]["dyson_ip"])

                    for attr in dir(device): 
                        val = getattr(device, attr)
                        if not attr.startswith("_") and type(val) in [int, float, bool]:
                            metrics.append(
                                    {
                                        'name': attr, 
                                        'value': val
                                    }
                                )
                    device.disconnect()
                except (DysonException, AttributeError) as e:
                    logger.error(f"Error when connecting to Dyson device: {e}")
                    return None

        else:

            try:
                device = ld.get_device(
                    self.dyson_serial,
                    self.dyson_credential,
                    self.dyson_device_type
                )
                device.connect(self.dyson_ip)

                for attr in dir(device): 
                    val = getattr(device, attr)
                    if not attr.startswith("_") and type(val) in [int, float, bool]:
                        metrics.append(
                                {
                                    'name': attr, 
                                    'value': val
                                }
                            )
                device.disconnect()
            except (DysonException, AttributeError) as e:
                logger.error(f"Error when connecting to Dyson device: {e}")
                return None

        return metrics

class SignalHandler():
    def __init__(self):
        self.shutdownCount = 0

        # Register signal handler
        signal.signal(signal.SIGINT, self._on_signal_received)
        signal.signal(signal.SIGTERM, self._on_signal_received)

    def is_shutting_down(self):
        return self.shutdownCount > 0

    def _on_signal_received(self, signal, frame):
        if self.shutdownCount > 1:
            logger.warn("Forcibly killing exporter")
            sys.exit(1)
        logger.info("Exporter is shutting down")
        self.shutdownCount += 1

def main():

    # Import env vars
    exporter_log_level = str(os.getenv("EXPORTER_LOG_LEVEL"))
    exporter_port = int(os.getenv("EXPORTER_PORT"))
    config_path = str(os.getenv("CONFIG_PATH"))
    dyson_serial = str(os.getenv("DYSON_SERIAL"))
    dyson_credential= str(os.getenv("DYSON_CREDENTIAL"))
    dyson_device_type = str(os.getenv("DYSON_DEVICE_TYPE"))
    dyson_ip = str(os.getenv("DYSON_IP"))

    # Init logger
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime) %(levelname) %(message)",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(exporter_log_level)
    
    # Register signal handler
    signal_handler = SignalHandler()
    
    # Register our custom collector
    logger.info("Exporter is starting up")
    REGISTRY.register(DysonMetricsCollector(config_path, dyson_serial, dyson_credential, dyson_device_type, dyson_ip))

    # Start server
    start_http_server(exporter_port)
    logger.info(
        f"Exporter listening on port {exporter_port}"
    )

    while not signal_handler.is_shutting_down():
        time.sleep(1)

    logger.info("Exporter has shutdown")