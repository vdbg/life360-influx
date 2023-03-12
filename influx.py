from influxdb_client import InfluxDBClient
import logging


class InfluxConnector:
    def __init__(self, influx_conf: dict):
        self.bucket: str = influx_conf["bucket"]
        self.token: str = influx_conf["token"]
        self.org: str = influx_conf["org"]
        self.url: str = influx_conf["url"]
        self.measurement: str = influx_conf["measurement"]
        self.no_op: bool = influx_conf["no_op"]
        logging.debug(f"Influx conf: url={self.url};bucket={self.bucket};org={self.org};measurement={self.measurement};no-op={self.no_op}")

    def __get_client(self) -> InfluxDBClient:
        return InfluxDBClient(url=self.url, token=self.token, org=self.org, debug=False)

    def add_samples(self, records) -> None:
        if not records:
            return

        logging.info(f"Importing {len(records)} record(s) to influx")
        logging.debug(records)

        if self.no_op:
            logging.warn("No-op mode, records not imported.")
            return

        with self.__get_client() as client:
            with client.write_api() as write_api:
                write_api.write(bucket=self.bucket, record=records)
