import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from abc import ABC
from typing import Generic, TypeVar
import sys


TIME_RE = re.compile(r"^(?P<hour>\d\d??):?(?P<minute>\d\d?)?(?:\s*(?P<p>pm?|am?))?$", re.IGNORECASE)

T = TypeVar('T')

class Converter(ABC, Generic[T]):
    def __init__(self):
        self.error = None
    
    def to_string(self, value: T) -> str:
        raise NotImplementedError
    
    def to_value(self, string: str) -> T | None:
        raise NotImplementedError


class StringConverter(Converter):
    def to_string(self, value: str) -> str:
        return value.strip()

    def to_value(self, string: str) -> str | None:
        return string.strip()


class TimeToNextDatetimeConverter(Converter):
    def __init__(self, datetime_format: str):
        super().__init__()
        if sys.platform != "win32":
            datetime_format = datetime_format.replace("#", "-")
        self.format = datetime_format

    def to_string(self, value: datetime) -> str:
        return datetime.strftime(value, self.format)

    def to_value(self, string: str) -> datetime | None:
        if not string:
            self.failure = ""
            return None
        self.error = None
        if match := TIME_RE.match(string):
            groups = match.groupdict()
            hour = int(groups["hour"])
            if hour < 1 or hour > 12:
                self.error = "Hour must be 1-12"
                return None
            minute = int(groups["minute"] or 0)
            if minute < 0 or minute > 59:
                self.error = "Minute must be 0-59"
                return None
            now = datetime.now()
            new_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            p = groups["p"]
            if p is None:
                for _ in range(2):
                    if new_time < now:
                        new_time += relativedelta(hours=12)
            else:
                if p.lower().startswith('p'):
                    new_time += relativedelta(hours=12)
                if new_time < now:
                    new_time += relativedelta(days=1)
            return new_time
        self.error = "Could not parse as time"
        return None
