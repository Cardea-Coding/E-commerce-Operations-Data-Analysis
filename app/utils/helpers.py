from datetime import datetime, timedelta


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间格式: {value}")


def time_range_or_default(start_time, end_time, window_days=30):
    end_dt = parse_datetime(end_time) if end_time else datetime.utcnow()
    start_dt = parse_datetime(start_time) if start_time else end_dt - timedelta(days=window_days)
    return start_dt, end_dt


def safe_divide(numerator, denominator):
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 4)