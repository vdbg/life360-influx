import datetime
import requests
import logging

# Docs for life 360 apis: https://krconv.github.io/life360-api-docs/
# Inspired from https://github.com/harperreed/life360-python/blob/master/life360.py


class Member:
    def __init__(self, conf: dict) -> None:
        self.name = self.__add_strings(conf["firstName"], conf["lastName"])
        self.has_location: bool = False
        location: dict = conf["location"]
        if not location:
            logging.warning(f"No location for {self.name}. Location sharing paused?")
            return
        self.latitude: float = float(location["latitude"])
        self.longitude: float = float(location["longitude"])
        self.start: datetime = self.__get_time(location, "startTimestamp")
        self.end: datetime = self.__get_time(location, "endTimestamp")
        self.address: str = self.__add_strings(location["address1"], location["address2"])
        self.has_location = True

    def __add_strings(self, s1: str, s2: str) -> str:
        if not s2 and not s1:
            return ""
        if not s2:
            return s1
        if not s1:
            return s2
        return s1 + " " + s2

    def __get_time(self, data: dict, key: str) -> datetime:
        return datetime.datetime.fromtimestamp(int(data[key]), tz=datetime.timezone.utc)

    def __str__(self) -> str:
        return f"{self.name} member at {self.address} ({self.latitude},{self.longitude}) from {self.start} to {self.end}"


class Circle:
    def __init__(self, conf: dict) -> None:
        self.id = conf["id"]
        self.name: str = conf["name"]
        self.members: list[Member] = [Member(x) for x in conf["members"]]
        self.members = [x for x in self.members if x.has_location]

    def __str__(self) -> str:
        return f"{self.name} circle ({self.id})"


class Life360Connector:
    def __init__(self, conf: dict) -> None:
        self.auth_token: str = conf["auth_token"]
        self.username: str = conf["username"]
        self.password: str = conf["password"]
        self.base_url: str = conf["base_url"]
        self.circles_url: str = conf["circles_url"]
        self.circle_url: str = conf["circle_url"]
        self.token_url: str = conf["token_url"]
        self.circle_ids: list[str] = conf["circle_ids"]
        self.access_token: str = None

    def __get_headers(self, auth: str) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": auth,
            "cache-control": "no-cache",
        }

    def __make_request(self, url, retry: bool = True):
        try:
            self.authenticate()
            r = requests.get(url, headers=self.__get_headers("bearer " + self.access_token))
            r.raise_for_status()
            return r.json()
        except:
            if retry:
                self.access_token = None
                self.authenticate(True)
                return self.__make_request(url, False)
            raise

    def authenticate(self, force: bool = False) -> None:
        if self.access_token and not force:
            return

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }

        self.access_token = None
        try:
            r = requests.post(self.base_url + self.token_url, data=data, headers=self.__get_headers("Basic " + self.auth_token))
            r.raise_for_status()
            self.access_token = r.json()["access_token"]
        except:
            logging.exception("Unable to authenticate")
            raise

    def get_circles(self) -> list[str]:
        if not self.circle_ids:
            r = self.__make_request(self.base_url + self.circles_url)
            self.circle_ids = [x["id"] for x in r["circles"]]
            logging.debug(f"Caching circle ids: {self.circle_ids}")
        return self.circle_ids

    def get_circle(self, circle_id) -> Circle:
        r = self.__make_request(self.base_url + self.circle_url + circle_id)
        return Circle(r)

    def get_records(self, measurement_name: str) -> list:
        records = []
        for circle_id in self.get_circles():
            logging.debug(f"Processing circleId {circle_id}")
            circle = self.get_circle(circle_id)
            for member in circle.members:
                logging.debug(f"Processing member {member}")
                for time in (member.start, member.end):
                    records.append(
                        {
                            "measurement": measurement_name,
                            "tags": {
                                "circle": circle.name,
                                "name": member.name,
                            },
                            "fields": {
                                "latitude": member.latitude,
                                "longitude": member.longitude,
                                "address": member.address,
                            },
                            "time": time,
                        }
                    )
        return records
