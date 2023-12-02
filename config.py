import logging
import os
import tomllib
from pathlib import Path


class Config:
    def __load__(file: str) -> dict[str, any]:
        try:
            with open(Path(__file__).with_name(file), "rb") as config_file:
                return tomllib.load(config_file)
        except FileNotFoundError as e:
            logging.warning(f"Missing {e.filename}.")
        return None

    def load(file: str, prefix: str) -> dict[str, any]:
        ret = Config.__load__("template." + file)
        if not ret:
            raise (f"File template.{file} required.")

        # overwrite template with config, if exists
        config = Config.__load__(file)
        if config:
            for k, v in config.items():
                for kk, vv in v.items():
                    ret[k][kk] = vv

        # overwrite with environment variables, if exist
        for k, v in ret.items():
            for kk, vv in v.items():
                key = f"{prefix}_{k}_{kk}".upper()
                ret[k][kk] = os.environ.get(key, vv)

        return ret
