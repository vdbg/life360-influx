#!/usr/bin/python3

import platform
import sys
import time
import tomllib
import logging

from influx import InfluxConnector
from life360 import Life360Connector
from pathlib import Path
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

SUPPORTED_PYTHON_MAJOR = 3
SUPPORTED_PYTHON_MINOR = 11

if sys.version_info < (SUPPORTED_PYTHON_MAJOR, SUPPORTED_PYTHON_MINOR):
    raise Exception(
        f"Python version {SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR} or later required. Current version: {platform.python_version()}."
    )


try:
    config = Config("config.toml", "life360_influx").load()

    main_conf = config["main"]
    logging.getLogger().setLevel(logging.getLevelName(main_conf["log_verbosity"]))
    loop_seconds: int = main_conf["loop_seconds"]
    logging.debug(f"CONFIG: {config}")

    influxConnector = InfluxConnector(config["influx"])
    life360Connector = Life360Connector(config["life360"])

    while True:
        try:
            influxConnector.add_samples(
                life360Connector.get_records(influxConnector.measurement)
            )
        except Exception as e:
            logging.exception(e)

        if not loop_seconds:
            exit(0)
        time.sleep(loop_seconds)

except Exception as e:
    logging.exception(e)
    exit(1)
