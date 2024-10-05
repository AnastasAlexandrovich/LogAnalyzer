import dataclasses
from datetime import datetime


@dataclasses.dataclass
class LogFileInfo:
    name: str = ""
    path: str = ""
    log_date: datetime | None = None
    count: int = 0
    request_time_total: float = 0


@dataclasses.dataclass
class UrlInfo:
    url: str
    request_time_list: list[float]
    count: int = 0
    # сколько раз встречается URL, в процентнах относительно общего числа запросов
    count_perc: float = 0
    # суммарный $request_time для данного URL’а, абсолютное значение
    time_sum: float = 0
    # суммарный $request_time для данного URL’а, в процентах относительно общего $request_time всех запросов
    time_perc: float = 0
    # средний $request_time для данного URL’а
    time_avg: float = 0
    #  максимальный $request_time для данного URL’а
    time_max: float = 0
    # медиана $request_time для данного URL’а
    time_med: float = 0

    def to_dict(self):
        return {
            "url": self.url,
            "count": self.count,
            "count_perc": self.count_perc,
            "time_sum": self.time_sum,
            "time_perc": self.time_perc,
            "time_avg": self.time_avg,
            "time_max": self.time_max,
            "time_med": self.time_med,
        }


@dataclasses.dataclass
class ParsedLine:
    url: str
    request_time: float
