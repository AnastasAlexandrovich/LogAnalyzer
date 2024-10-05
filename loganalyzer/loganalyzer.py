import argparse
import gzip
import os
import re
import datetime
import statistics

import structlog
import logging
import yaml
from dto.dto import UrlInfo, ParsedLine, LogFileInfo


DEFAULT_CONFIG_PATH = "config/default-config.yaml"

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO), processors=[structlog.processors.add_log_level, structlog.processors.JSONRenderer()]
)

logger = structlog.getLogger()


def prepare_result_config(config_path):
    with open(DEFAULT_CONFIG_PATH) as f:
        default_config = yaml.safe_load(f)
    if config_path != DEFAULT_CONFIG_PATH:
        try:
            with open(config_path) as f:
                custom_config = yaml.safe_load(f)
            default_config.update(custom_config)
        except Exception as e:
            logger.exception("Error while preparing the config", error=e)
            return None
    logger.info("Result config is prepared", config=default_config)
    return default_config


def get_latest_log(log_dir_files: list[str]) -> LogFileInfo:
    pattern = r"nginx-access-ui\.log-((\d{8}\.gz)|(\d{8}))"
    latest_log = LogFileInfo()
    for filename in log_dir_files:
        res = re.search(pattern, filename)
        if res:
            format = "%Y%m%d"
            if "gz" in filename:
                log_date = datetime.datetime.strptime(res.groups()[0].split(".")[0], format)
            else:
                log_date = datetime.datetime.strptime(res.groups()[0], format)
            if not latest_log.log_date or log_date > latest_log.log_date:
                latest_log.log_date = log_date
                latest_log.name = filename
    logger.info("Found latest log", latest_log=latest_log.name)
    return latest_log


def parse_log_file(latest_log_path):

    file_open_function = gzip.open if "gz" in latest_log_path else open
    log_file_size = 0
    url_pattern = r"\"(\w*\ \/(.*?))\""
    time_pattern = r"(\d+.\d+)$"

    with file_open_function(latest_log_path, "r") as f:
        for line in f:
            log_file_size += 1
            url_search = re.search(url_pattern, line)
            request_time_search = re.search(time_pattern, line)

            if url_search and request_time_search:

                url = url_search.groups()[1].split(" ")[0]
                request_time = float(request_time_search.groups()[0])

                yield ParsedLine(url=url, request_time=request_time)


def get_report_data(parse_function, latest_log: LogFileInfo):
    report_lines = {}
    log_file_size = 0
    for parsed_line in parse_function(latest_log.path):
        log_file_size += 1
        parsed_line_url = parsed_line.url
        request_time = parsed_line.request_time
        latest_log.request_time_total += request_time
        if report_lines.get(parsed_line_url):
            report_lines[parsed_line_url].request_time_list.append(request_time)
            report_lines[parsed_line_url].count += 1
        else:
            report_lines[parsed_line_url] = UrlInfo(url=parsed_line_url, request_time_list=[request_time], count=1)
    latest_log.count = log_file_size
    return list(report_lines.values())


def analyze_data(log_file_size: int, total_request_time: float, report_data: list[UrlInfo]):

    for report in report_data:
        report.time_sum = sum(report.request_time_list)
        report.time_avg = report.time_sum / len(report.request_time_list)
        report.count_perc = report.count / log_file_size
        report.time_max = max(report.request_time_list)
        report.time_med = statistics.median(report.request_time_list)
        report.time_perc = report.time_sum / total_request_time


def prepare_report(report_path: str, log_date: datetime, log_report):
    with open("report-template/report.html", "r") as f:
        report_string = f.read()

    new_report = report_string.replace("$table_json", log_report)

    try:
        final_report_path = report_path + "/report-" + log_date.strftime("%Y-%m-%d") + ".html"
        logger.info("Write Report", report_path=final_report_path)
        with open(final_report_path, "w") as f:
            f.write(new_report)
    except FileNotFoundError as e:
        logger.exception("Error occurred while saving the report", error=e)


def main(config_path):
    config = prepare_result_config(config_path)
    if not config:
        return None
    log_dir = config.get("LOG_DIR")
    try:
        log_dir_files = os.listdir(log_dir)
    except FileNotFoundError as e:
        logger.exception("Can not find a log file", error=e)
        return None
    except NotADirectoryError as e:
        logger.exception("Can not find a log dir", error=e)
        return None

    latest_log = get_latest_log(log_dir_files)
    latest_log.path = log_dir + "/" + latest_log.name

    report_data = get_report_data(parse_log_file, latest_log)

    analyze_data(latest_log.count, latest_log.request_time_total, report_data)

    log_report = str([elem.to_dict() for elem in report_data])

    prepare_report(config.get("REPORT_DIR"), latest_log.log_date, log_report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Say hello")
    parser.add_argument("--config", help="Path to log analyzer config file", default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    main(args.config)
