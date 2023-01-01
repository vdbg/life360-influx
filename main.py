#!/usr/bin/python3

import platform
import sys
import time
import tomllib
import logging

from influx import InfluxConnector
from life360 import Life360Connector
from pathlib import Path

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


def get_config():
    CONFIG_FILE = "config.toml"
    try:
        with open(Path(__file__).with_name(CONFIG_FILE), "rb") as config_file:
            config = tomllib.load(config_file)

            if not config:
                raise ValueError(f"Invalid {CONFIG_FILE}. See template.{CONFIG_FILE}.")

            for name in {"influx", "life360", "main"}:
                if name not in config:
                    raise ValueError(f"Invalid {CONFIG_FILE}: missing section {name}.")

            return config
    except FileNotFoundError as e:
        logging.error(f"Missing {e.filename}.")
        exit(2)


SUPPORTED_PYTHON_MAJOR = 3
SUPPORTED_PYTHON_MINOR = 11

if sys.version_info < (SUPPORTED_PYTHON_MAJOR, SUPPORTED_PYTHON_MINOR):
    raise Exception(f"Python version {SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR} or later required. Current version: {platform.python_version()}.")


try:
    config = get_config()

    main_conf = config["main"]
    logging.getLogger().setLevel(logging.getLevelName(main_conf["logverbosity"]))
    loop_seconds: int = main_conf["loop_seconds"]

    influxConnector = InfluxConnector(config["influx"])
    life360Connector = Life360Connector(config["life360"])

    while True:
        try:
            influxConnector.add_samples(life360Connector.get_records("location"))
        except Exception as e:
            logging.exception(e)

        if not loop_seconds:
            exit(0)
        time.sleep(loop_seconds)

except Exception as e:
    logging.exception(e)
    exit(1)
